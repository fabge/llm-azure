"""Azure AI Foundry Anthropic provider for LLM."""

from llm_anthropic import ClaudeMessages


class AzureAnthropicChat(ClaudeMessages):
    """Chat model for Anthropic models on Azure AI Foundry with Entra ID auth."""

    # Override parent - we don't always need a key
    needs_key = None
    key_env_var = None

    def __init__(
        self,
        model_id: str,
        model_name: str,
        endpoint: str,
        api_key_name: str | None = None,
    ):
        # Initialize parent with Azure endpoint
        super().__init__(
            model_id=model_id,
            claude_model_id=model_name,
            supports_images=True,
            supports_pdf=True,
            base_url=endpoint,
        )
        # Override parent's model_id (which adds "anthropic/" prefix)
        self.model_id = model_id
        self.endpoint = endpoint
        self.api_key_name = api_key_name

        if api_key_name:
            self.needs_key = api_key_name
            self.key_env_var = f"LLM_{api_key_name.upper()}_KEY"

    def _get_azure_client(self, key=None):
        """Get AnthropicFoundry client with API key or Entra ID auth."""
        from anthropic import AnthropicFoundry

        if self.api_key_name and key:
            return AnthropicFoundry(api_key=key, base_url=self.endpoint)
        else:
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider

            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default",
            )
            return AnthropicFoundry(
                azure_ad_token_provider=token_provider,
                base_url=self.endpoint,
            )

    def execute(self, prompt, stream, response, conversation, key=None):
        """Execute using Azure client instead of standard Anthropic client."""
        # Get our Azure client instead of the parent's Anthropic client
        client = self._get_azure_client(
            self.get_key(key) if self.api_key_name else None,
        )

        # Reuse parent's message/kwargs building
        kwargs = self.build_kwargs(prompt, conversation)
        prefill_text = self.prefill_text(prompt)

        # Handle beta features
        messages_client = client.beta.messages if "betas" in kwargs else client.messages

        if stream:
            with messages_client.stream(**kwargs) as stream_response:
                if prefill_text:
                    yield prefill_text
                for chunk in stream_response:
                    if hasattr(chunk, "delta"):
                        delta = chunk.delta
                        if hasattr(delta, "text"):
                            yield delta.text
                        elif hasattr(delta, "partial_json") and prompt.schema:
                            yield delta.partial_json
                # Record usage
                last_message = self._model_dump_suppress_warnings(
                    stream_response.get_final_message(),
                )
                response.response_json = last_message
                if self.add_tool_usage(response, last_message):
                    yield " "
        else:
            completion = messages_client.create(**kwargs)
            text = "".join(
                [item.text for item in completion.content if hasattr(item, "text")],
            )
            yield prefill_text + text
            response.response_json = completion.model_dump()
            self.add_tool_usage(response, response.response_json)
