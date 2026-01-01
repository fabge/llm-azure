"""Azure AI Foundry plugin for LLM.

Supports multiple providers with Entra ID authentication:
- anthropic: Claude models (requires: pip install llm-azure[anthropic])
- openai: GPT, Mistral, Llama and other OpenAI-compatible models
"""

import llm
import yaml
from llm import hookimpl


def _load_config():
    """Load config from azure/config.yaml."""
    azure_path = llm.user_dir() / "azure" / "config.yaml"
    if not azure_path.exists():
        return []

    with open(azure_path) as f:
        models = yaml.safe_load(f)

    return models or []


@hookimpl
def register_models(register):
    models = _load_config()

    for model in models:
        provider = model.get("provider")
        aliases = model.pop("aliases", [])

        if provider == "anthropic":
            from llm_azure.anthropic import AzureAnthropicChat

            register(
                AzureAnthropicChat(
                    model_id=model["model_id"],
                    model_name=model["model_name"],
                    endpoint=model["endpoint"],
                    api_key_name=model.get("api_key_name"),
                ),
                aliases=aliases,
            )
        elif provider == "openai":
            from llm_azure.openai import AzureOpenAIChat

            register(
                AzureOpenAIChat(
                    model_id=model["model_id"],
                    model_name=model["model_name"],
                    endpoint=model["endpoint"],
                    api_key_name=model.get("api_key_name"),
                    supports_images=model.get("supports_images", True),
                ),
                aliases=aliases,
            )
