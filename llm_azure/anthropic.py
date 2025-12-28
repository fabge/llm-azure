"""Azure AI Foundry Anthropic provider for LLM."""

import llm
from llm import Model


class AzureAnthropicChat(Model):
    """Chat model for Anthropic models on Azure AI Foundry."""

    can_stream = True

    def __init__(
        self,
        model_id: str,
        model_name: str,
        endpoint: str,
        api_key_name: str | None = None,
    ):
        self.model_id = model_id
        self.model_name = model_name
        self.endpoint = endpoint
        self.api_key_name = api_key_name

        # Set needs_key for LLM's key management if using API key auth
        if api_key_name:
            self.needs_key = api_key_name
            self.key_env_var = f"LLM_{api_key_name.upper()}_KEY"

    def _get_client(self, key=None):
        """Get Anthropic client with API key or Entra ID auth (lazy import)."""
        from anthropic import AnthropicFoundry

        if self.api_key_name and key:
            # Use API key auth
            return AnthropicFoundry(
                api_key=key,
                base_url=self.endpoint,
            )
        else:
            # Use Entra ID auth
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider

            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default",
            )

            return AnthropicFoundry(
                azure_ad_token_provider=token_provider,
                base_url=self.endpoint,
            )

    def execute(self, prompt, stream, response, conversation):
        key = self.get_key() if self.api_key_name else None
        client = self._get_client(key)

        messages = []
        if conversation:
            for prev in conversation.responses:
                messages.append({"role": "user", "content": prev.prompt.prompt})
                messages.append({"role": "assistant", "content": prev.text()})
        messages.append({"role": "user", "content": prompt.prompt})

        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": prompt.options.max_tokens or 4096,
        }

        if prompt.system:
            kwargs["system"] = prompt.system

        if stream:
            with client.messages.stream(**kwargs) as stream_response:
                yield from stream_response.text_stream
        else:
            result = client.messages.create(**kwargs)
            yield result.content[0].text

    class Options(llm.Options):
        max_tokens: int | None = None
