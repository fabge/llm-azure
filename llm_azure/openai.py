"""Azure AI Foundry OpenAI provider for LLM with Entra ID auth."""

from llm.default_plugins.openai_models import Chat, _Shared


class AzureOpenAIShared(_Shared):
    """Shared functionality for Azure OpenAI models with Entra ID auth."""

    # Override parent class - we don't always need a key
    needs_key = None
    key_env_var = None

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

    def get_client(self, key=None, async_=False):
        """Get OpenAI client with API key or Entra ID auth."""
        if async_:
            from openai import AsyncOpenAI as ClientClass
        else:
            from openai import OpenAI as ClientClass

        if self.api_key_name and key:
            return ClientClass(api_key=key, base_url=self.endpoint)
        else:
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider

            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default",
            )
            return ClientClass(api_key=token_provider(), base_url=self.endpoint)


class AzureOpenAIChat(AzureOpenAIShared, Chat):
    """Chat model for OpenAI models on Azure AI Foundry with Entra ID auth."""

    def __init__(
        self,
        model_id: str,
        model_name: str,
        endpoint: str,
        api_key_name: str | None = None,
        supports_images: bool = True,
    ):
        # Initialize shared functionality
        AzureOpenAIShared.__init__(
            self,
            model_id=model_id,
            model_name=model_name,
            endpoint=endpoint,
            api_key_name=api_key_name,
        )
        # Initialize Chat with schema support
        Chat.__init__(
            self,
            model_id=model_id,
            model_name=model_name,
            supports_schema=True,
            supports_tools=True,
        )
        # Set attachment types for vision support
        if supports_images:
            self.attachment_types = {
                "image/png",
                "image/jpeg",
                "image/webp",
                "image/gif",
                "application/pdf",
            }
