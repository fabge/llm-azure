import json

import llm


def test_azure_tool_calling():
    """Test that Azure handles tool calling."""
    model = llm.get_model()  # Uses default model

    def multiply(a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b

    response = model.chain("What is 7 * 6?", tools=[multiply])
    output = response.text()

    assert "42" in output


def test_azure_schema_output():
    """Test that Azure handles structured output with schema."""
    model = llm.get_model()  # Uses default model

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name", "age"],
    }

    response = model.prompt(
        "Generate a person named Alice who is 30 years old",
        schema=schema,
    )
    result = json.loads(response.text())

    assert result["name"] == "Alice"
    assert result["age"] == 30
