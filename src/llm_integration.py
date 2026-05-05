"""
llm_integration.py

Thin abstraction layer over the OpenAI chat completions API.
Responsibilities:
  - Initialise API clients from environment variables
  - Send chat completion requests with configurable parameters
  - Handle retries, rate limiting, and error responses
"""

import os
import time
import logging
from typing import Any, Optional

from dotenv import load_dotenv
from openai import (
    OpenAI,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    BadRequestError,
)

load_dotenv()
logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 60
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BACKOFF_SECONDS = 1.0
_DEFAULT_MAX_PROMPT_CHARS = 80_000
_DEFAULT_MAX_OUTPUT_TOKENS = 1_800


class ContentGeneratorError(Exception):
    """Raised when content generation fails in a way the caller should handle explicitly."""


class OpenAIWrapper:
    """Wrapper for OpenAI API calls with standardized errors and retry logic."""

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        backoff_seconds: float = _DEFAULT_BACKOFF_SECONDS,
        client: Optional[Any] = None,
    ):
        if not api_key:
            raise ContentGeneratorError(
                "OPENAI_API_KEY is not set.\n"
                "  Fix: copy .env.example to .env and add your key:\n"
                "       OPENAI_API_KEY=sk-..."
            )
        if not api_key.startswith("sk-"):
            raise ContentGeneratorError(
                "OPENAI_API_KEY looks malformed (should start with 'sk-').\n"
                "  Fix: check the value in your .env file."
            )

        self.api_key = api_key
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.max_retries = max(1, max_retries)
        self.backoff_seconds = max(0.0, backoff_seconds)
        self.max_prompt_chars = int(os.getenv("MAX_LLM_PROMPT_CHARS", str(_DEFAULT_MAX_PROMPT_CHARS)))
        self.max_output_tokens = int(os.getenv("MAX_LLM_OUTPUT_TOKENS", str(_DEFAULT_MAX_OUTPUT_TOKENS)))
        self.client = client or OpenAI(api_key=api_key)
        logger.info(
            "OpenAIWrapper initialized model=%s max_retries=%s backoff_seconds=%s max_prompt_chars=%s max_output_tokens=%s",
            self.model,
            self.max_retries,
            self.backoff_seconds,
            self.max_prompt_chars,
            self.max_output_tokens,
        )

    def retry_delay(self, attempt: int) -> float:
        """Return exponential backoff delay for an attempt number."""
        return self.backoff_seconds * (2 ** (attempt - 1))

    def success_response(self, content: str, attempts: int) -> dict[str, Any]:
        """Create a standardized successful response."""
        logger.info("OpenAI request succeeded model=%s attempts=%s content_chars=%s", self.model, attempts, len(content))
        return {
            "status": "success",
            "content": content,
            "attempts": attempts,
            "model": self.model,
        }

    def error_response(self, error: Exception, attempts: int) -> dict[str, Any]:
        """Create a standardized error response."""
        logger.error("OpenAI request failed model=%s attempts=%s error_type=%s error=%s", self.model, attempts, type(error).__name__, error)
        return {
            "status": "error",
            "error_type": type(error).__name__,
            "error": self.format_error(error),
            "attempts": attempts,
            "model": self.model,
        }

    def format_error(self, error: Exception) -> str:
        """Return an actionable message for API/client errors."""
        if isinstance(error, AuthenticationError):
            return (
                "Invalid OpenAI API key.\n"
                "  Fix: check OPENAI_API_KEY in your .env file.\n"
                "  Get a key at: https://platform.openai.com/api-keys"
            )
        if isinstance(error, RateLimitError):
            return (
                "OpenAI rate limit exceeded.\n"
                "  Fix: wait a minute, reduce request volume, or check your usage."
            )
        if isinstance(error, APITimeoutError):
            return (
                f"OpenAI request timed out after {_TIMEOUT_SECONDS}s.\n"
                "  Fix: the prompt may be too large, or OpenAI is slow. Try again shortly."
            )
        if isinstance(error, APIConnectionError):
            return "Could not reach OpenAI.\n  Fix: check your internet connection, then try again."
        if isinstance(error, BadRequestError):
            return (
                f"OpenAI rejected the request: {error}\n"
                "  Fix: the prompt may exceed the model's context limit. Try reducing context."
            )
        if isinstance(error, ContentGeneratorError):
            return str(error)
        return f"Unexpected API error: {error}"

    def extract_content(self, response: Any) -> str:
        """Extract assistant text from an OpenAI response object."""
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as error:
            raise ContentGeneratorError(
                "OpenAI response did not include choices[0].message.content.\n"
                "  Fix: inspect the raw provider response shape."
            ) from error

        if not content or not content.strip():
            raise ContentGeneratorError("OpenAI returned an empty response. Try rephrasing the prompt.")
        return content

    def create_chat_completion(self, prompt: str) -> dict[str, Any]:
        """Create one chat completion with retry and standardized response data."""
        if not prompt or not prompt.strip():
            logger.error("OpenAI request skipped: empty prompt")
            return self.error_response(ContentGeneratorError("Prompt is empty — nothing was sent to the API."), 0)
        if len(prompt) > self.max_prompt_chars:
            logger.error("OpenAI request skipped: prompt too large chars=%s limit=%s", len(prompt), self.max_prompt_chars)
            return self.error_response(
                ContentGeneratorError(
                    f"Prompt is too large for configured cost controls ({len(prompt)} chars > {self.max_prompt_chars})."
                ),
                0,
            )

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info("Calling OpenAI chat completion model=%s attempt=%s/%s prompt_chars=%s", self.model, attempt, self.max_retries, len(prompt))
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.max_output_tokens,
                    timeout=_TIMEOUT_SECONDS,
                )
                return self.success_response(self.extract_content(response), attempt)
            except (AuthenticationError, BadRequestError) as error:
                last_error = error
                logger.error("OpenAI non-retryable error model=%s attempt=%s/%s error=%s", self.model, attempt, self.max_retries, error)
                break
            except Exception as error:
                last_error = error
                logger.error("OpenAI chat completion attempt failed model=%s attempt=%s/%s error=%s", self.model, attempt, self.max_retries, error)
                if attempt < self.max_retries:
                    delay = self.retry_delay(attempt)
                    logger.info("Retrying OpenAI request in %s seconds", delay)
                    time.sleep(delay)

        return self.error_response(last_error or ContentGeneratorError("Unknown OpenAI API error."), self.max_retries)

    def generate_description(self, prompt: str) -> dict[str, Any]:
        """Generate content for a prompt with retry and standardized response data."""
        return self.create_chat_completion(prompt)


class ContentGenerator:
    """Simple OpenAI wrapper that loads credentials from .env and generates text."""

    def __init__(
        self,
        model: Optional[str] = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        backoff_seconds: float = _DEFAULT_BACKOFF_SECONDS,
        wrapper: Optional[OpenAIWrapper] = None,
    ):
        api_key = os.getenv("OPENAI_API_KEY")
        self.wrapper = wrapper or OpenAIWrapper(
            api_key=api_key or "",
            model=model,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )

    def generate_content(self, prompt: str) -> str:
        """
        Send a prompt to OpenAI and return the generated text.

        Args:
            prompt: The full prompt string (system + user context already combined).

        Returns:
            The model's text response.

        Raises:
            ContentGeneratorError: For unrecoverable failures the caller should surface.
        """
        result = self.wrapper.generate_description(prompt)
        if result["status"] == "success":
            return result["content"]
        logger.error("ContentGenerator failed with standardized wrapper error: %s", result)
        raise ContentGeneratorError(result["error"])
