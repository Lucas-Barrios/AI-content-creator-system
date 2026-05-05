"""
llm_integration.py

Thin abstraction layer over LLM provider APIs (Anthropic Claude, OpenAI GPT).
Responsibilities:
  - Initialise API clients from environment variables
  - Send chat completion requests with configurable parameters
  - Handle retries, rate limiting, and error responses
  - Support model switching without changing calling code
"""

import os
import time

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

_TIMEOUT_SECONDS = 60
_RATE_LIMIT_RETRY_WAIT = 15  # seconds to wait before one automatic retry


class ContentGeneratorError(Exception):
    """Raised when content generation fails in a way the caller should handle explicitly."""


class ContentGenerator:
    """Simple OpenAI wrapper that loads credentials from .env and generates text."""

    def __init__(self, model: str = "gpt-4o-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
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
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_content(self, prompt: str, _retry: bool = True) -> str:
        """
        Send a prompt to OpenAI and return the generated text.

        Args:
            prompt: The full prompt string (system + user context already combined).

        Returns:
            The model's text response.

        Raises:
            ContentGeneratorError: For unrecoverable failures the caller should surface.
        """
        if not prompt or not prompt.strip():
            raise ContentGeneratorError("Prompt is empty — nothing was sent to the API.")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=_TIMEOUT_SECONDS,
            )
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise ContentGeneratorError(
                    "OpenAI returned an empty response. Try rephrasing the prompt."
                )
            return content

        except AuthenticationError:
            raise ContentGeneratorError(
                "Invalid OpenAI API key.\n"
                "  Fix: check OPENAI_API_KEY in your .env file.\n"
                "  Get a key at: https://platform.openai.com/api-keys"
            )
        except RateLimitError:
            if _retry:
                print(f"  Rate limit hit — waiting {_RATE_LIMIT_RETRY_WAIT}s before retrying...")
                time.sleep(_RATE_LIMIT_RETRY_WAIT)
                return self.generate_content(prompt, _retry=False)
            raise ContentGeneratorError(
                "OpenAI rate limit exceeded and retry failed.\n"
                "  Fix: wait a minute, or check your usage at https://platform.openai.com/usage"
            )
        except APITimeoutError:
            raise ContentGeneratorError(
                f"OpenAI request timed out after {_TIMEOUT_SECONDS}s.\n"
                "  Fix: the prompt may be too large, or OpenAI is slow — try again shortly."
            )
        except APIConnectionError:
            raise ContentGeneratorError(
                "Could not reach OpenAI.\n"
                "  Fix: check your internet connection, then try again."
            )
        except BadRequestError as e:
            raise ContentGeneratorError(
                f"OpenAI rejected the request: {e}\n"
                "  Fix: the prompt may exceed the model's context limit. "
                "Try reducing the knowledge base context."
            )
        except Exception as e:
            raise ContentGeneratorError(f"Unexpected API error: {e}")


def get_client(provider: str = "anthropic"):
    """
    Return an initialised API client for the specified provider.

    Args:
        provider: 'anthropic' or 'openai'
    """
    pass


def generate(
    system_prompt: str,
    user_prompt: str,
    model: str = "claude-opus-4-7",
    max_tokens: int = 2048,
    temperature: float = 0.7,
    provider: str = "anthropic",
) -> str:
    """
    Send a prompt to the LLM and return the text response.

    Args:
        system_prompt: Instructions that define the assistant's role and constraints.
        user_prompt: The specific request, including injected context.
        model: Model identifier string.
        max_tokens: Maximum tokens in the completion.
        temperature: Sampling temperature (0 = deterministic, 1 = creative).
        provider: 'anthropic' or 'openai'.

    Returns:
        The model's text response.
    """
    pass


def count_tokens(text: str, model: str = "claude-opus-4-7") -> int:
    """Estimate token count for a string (useful for chunking and cost tracking)."""
    pass
