"""Test Azure AI Foundry with Anthropic models via LLM plugin."""

import llm


def test_claude_chat():
    """Test Claude model via LLM plugin."""
    model = llm.get_model("claude-opus")
    response = model.prompt("What is 2+2? Reply with just the number.")
    text = response.text()

    print(f"Response: {text}")
    assert "4" in text


def test_claude_streaming():
    """Test Claude model streaming via LLM plugin."""
    model = llm.get_model("claude-opus")
    response = model.prompt("Count from 1 to 3, one number per line")

    chunks = list(response)
    text = "".join(chunks)

    print(f"Response: {text}")
    assert "1" in text
    assert "2" in text
    assert "3" in text


if __name__ == "__main__":
    test_claude_chat()
    print("Chat test passed!")
    test_claude_streaming()
    print("Streaming test passed!")
