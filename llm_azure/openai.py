"""Azure AI Foundry OpenAI provider for LLM with Entra ID auth."""

import llm
from llm import Model


class AzureOpenAIChat(Model):
    """Chat model for OpenAI models on Azure AI Foundry with Entra ID auth."""

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

        if api_key_name:
            self.needs_key = api_key_name
            self.key_env_var = f"LLM_{api_key_name.upper()}_KEY"

    def _get_client(self, key=None):
        """Get OpenAI client with API key or Entra ID auth (lazy import)."""
        from openai import OpenAI

        if self.api_key_name and key:
            # Use API key auth
            return OpenAI(
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

            return OpenAI(
                api_key=token_provider(),
                base_url=self.endpoint,
            )

    def execute(self, prompt, stream, response, conversation):
        key = self.get_key() if self.api_key_name else None
        client = self._get_client(key)

        messages = []
        if prompt.system:
            messages.append({"role": "system", "content": prompt.system})
        if conversation:
            for prev in conversation.responses:
                messages.append({"role": "user", "content": prev.prompt.prompt})
                messages.append({"role": "assistant", "content": prev.text()})
        messages.append({"role": "user", "content": prompt.prompt})

        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
        }

        if prompt.options.max_tokens:
            kwargs["max_tokens"] = prompt.options.max_tokens

        if stream:
            completion = client.chat.completions.create(**kwargs)
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            completion = client.chat.completions.create(**kwargs)
            yield completion.choices[0].message.content

    class Options(llm.Options):
        max_tokens: int | None = None
