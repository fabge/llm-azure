"""Integration tests for Azure OpenAI models.

These tests require actual Azure credentials and model setup.
Run with: python tests/test_azure_openai.py
"""

import llm


def test_openai_chat():
    """Test OpenAI model via LLM plugin."""
    model = llm.get_model("azure-gpt4o")
    response = model.prompt("What is 2+2? Reply with just the number.")
    text = response.text()

    print(f"Response: {text}")
    assert "4" in text


def test_openai_streaming():
    """Test OpenAI model streaming."""
    model = llm.get_model("azure-gpt4o")
    response = model.prompt("Count from 1 to 3, one number per line")

    chunks = list(response)
    text = "".join(chunks)

    print(f"Response: {text}")
    assert "1" in text
    assert "2" in text
    assert "3" in text


def test_openai_schema():
    """Test OpenAI model with structured JSON output."""
    model = llm.get_model("azure-gpt4o")
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "integer"}},
        "required": ["answer"],
    }
    response = model.prompt("What is 2+2?", schema=schema)
    text = response.text()

    print(f"Response: {text}")
    assert '"answer"' in text
    assert "4" in text


if __name__ == "__main__":
    test_openai_chat()
    print("Chat test passed!")
    test_openai_streaming()
    print("Streaming test passed!")
    test_openai_schema()
    print("Schema test passed!")
