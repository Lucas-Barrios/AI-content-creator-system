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
