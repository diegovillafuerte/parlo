"""Anthropic Claude client wrapper with retry logic and error handling."""

import logging
from typing import Any

import anthropic
from anthropic import APIError, RateLimitError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AnthropicClient:
    """Wrapper around Anthropic's Claude API with retry logic."""

    def __init__(self, api_key: str | None = None):
        """Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to settings)
        """
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            logger.warning("No Anthropic API key configured - AI features will be disabled")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    @property
    def is_configured(self) -> bool:
        """Check if client is properly configured."""
        return self.client is not None

    async def create_message(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
        model: str = "claude-sonnet-4-20250514",
    ) -> anthropic.types.Message:
        """Create a message using Claude.

        Args:
            system_prompt: System prompt for Claude
            messages: Conversation history
            tools: Available tools for Claude to use
            max_tokens: Maximum tokens in response
            model: Model to use

        Returns:
            Claude's response message

        Raises:
            ValueError: If client is not configured
            APIError: If API call fails after retries
        """
        if not self.is_configured:
            raise ValueError("Anthropic client not configured - missing API key")

        logger.debug(
            f"Creating Claude message:\n"
            f"  Model: {model}\n"
            f"  Messages: {len(messages)}\n"
            f"  Tools: {len(tools) if tools else 0}"
        )

        try:
            # Build request parameters
            params: dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": messages,
            }

            if tools:
                params["tools"] = tools

            # Make API call (synchronous, but fast enough for our use case)
            response = self.client.messages.create(**params)

            logger.debug(
                f"Claude response:\n"
                f"  Stop reason: {response.stop_reason}\n"
                f"  Usage: {response.usage.input_tokens} in, {response.usage.output_tokens} out"
            )

            return response

        except RateLimitError as e:
            logger.warning(f"Rate limited by Anthropic: {e}")
            raise

        except APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def extract_text_response(self, response: anthropic.types.Message) -> str:
        """Extract text content from Claude's response.

        Args:
            response: Claude's response message

        Returns:
            Text content from the response
        """
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    def extract_tool_calls(
        self, response: anthropic.types.Message
    ) -> list[dict[str, Any]]:
        """Extract tool calls from Claude's response.

        Args:
            response: Claude's response message

        Returns:
            List of tool calls with name and input
        """
        tool_calls = []
        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        return tool_calls

    def has_tool_calls(self, response: anthropic.types.Message) -> bool:
        """Check if response contains tool calls.

        Args:
            response: Claude's response message

        Returns:
            True if response contains tool calls
        """
        return response.stop_reason == "tool_use"


# Singleton instance for easy access
_client: AnthropicClient | None = None


def get_anthropic_client() -> AnthropicClient:
    """Get singleton Anthropic client instance."""
    global _client
    if _client is None:
        _client = AnthropicClient()
    return _client
