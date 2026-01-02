"""Test model capabilities (attachments, schema, tools)."""

from llm_azure.anthropic import AzureAnthropicChat
from llm_azure.openai import AzureOpenAIChat


def test_openai_supports_attachments():
    """OpenAI models should support image and PDF attachments."""
    model = AzureOpenAIChat(
        model_id="test-gpt4o",
        model_name="gpt-4o",
        endpoint="https://example.com",
    )
    assert model.attachment_types == {
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
        "application/pdf",
    }


def test_openai_supports_schema():
    """OpenAI models should support structured JSON output."""
    model = AzureOpenAIChat(
        model_id="test-gpt4o",
        model_name="gpt-4o",
        endpoint="https://example.com",
    )
    assert model.supports_schema is True


def test_openai_supports_tools():
    """OpenAI models should support function calling."""
    model = AzureOpenAIChat(
        model_id="test-gpt4o",
        model_name="gpt-4o",
        endpoint="https://example.com",
    )
    assert model.supports_tools is True


def test_anthropic_supports_attachments():
    """Anthropic models should support image and PDF attachments."""
    model = AzureAnthropicChat(
        model_id="test-claude",
        model_name="claude-opus-4-5",
        endpoint="https://example.com",
    )
    assert model.attachment_types == {
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
        "application/pdf",
    }


def test_anthropic_supports_schema():
    """Anthropic models should support structured JSON output."""
    model = AzureAnthropicChat(
        model_id="test-claude",
        model_name="claude-opus-4-5",
        endpoint="https://example.com",
    )
    assert model.supports_schema is True


def test_anthropic_supports_tools():
    """Anthropic models should support function calling."""
    model = AzureAnthropicChat(
        model_id="test-claude",
        model_name="claude-opus-4-5",
        endpoint="https://example.com",
    )
    assert model.supports_tools is True


if __name__ == "__main__":
    test_openai_supports_attachments()
    test_openai_supports_schema()
    test_openai_supports_tools()
    print("OpenAI capability tests passed!")

    test_anthropic_supports_attachments()
    test_anthropic_supports_schema()
    test_anthropic_supports_tools()
    print("Anthropic capability tests passed!")
