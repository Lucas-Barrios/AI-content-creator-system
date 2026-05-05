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

from dotenv import load_dotenv
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError

load_dotenv()


class ContentGenerator:
    """Simple OpenAI wrapper that loads credentials from .env and generates text."""

    def __init__(self, model: str = "gpt-4o"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_content(self, prompt: str) -> str:
        """
        Send a prompt to OpenAI and return the generated text.

        Args:
            prompt: The full prompt string (system + user context already combined).

        Returns:
            The model's text response, or an error message string if the call fails.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

        except AuthenticationError:
            return "Error: Invalid OpenAI API key. Check OPENAI_API_KEY in your .env file."
        except RateLimitError:
            return "Error: OpenAI rate limit reached. Wait a moment and try again."
        except APIConnectionError:
            return "Error: Could not connect to OpenAI. Check your internet connection."
        except Exception as e:
            return f"Error: Unexpected issue — {e}"


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
