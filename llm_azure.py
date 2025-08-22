import os
import sys
from typing import Iterable, Iterator, List, Union

import llm
import yaml
from llm import EmbeddingModel, hookimpl
from llm.default_plugins.openai_models import AsyncChat, Chat, _Shared, not_nulls
from openai import AsyncAzureOpenAI, AzureOpenAI


CONFIG_TEMPLATE = """
- model_id: azure-gpt-5-mini
  model_name: gpt-5-mini
  api_base: https://your_deployment.cognitiveservices.azure.com/
  api_version: '2024-12-01-preview'

- model_id: text-embedding-3-small
  embedding_model: true
  model_name: text-embedding-3-small
  api_base: https://your_deployment.openai.azure.com/
  api_version: "2024-02-01"
""".lstrip()


def get_azure_models(azure_path):
    try:
        with open(azure_path, "rt") as f:
            content = f.read()
            models = yaml.safe_load(content) or []
    except FileNotFoundError:
        with open(azure_path, "w") as f:
            f.write(CONFIG_TEMPLATE)
        content = CONFIG_TEMPLATE
        models = yaml.safe_load(content)

    if "your_deployment" in content or not models:
        print(
            "    Your Azure config file needs to be initialized with your deployment values. Find yours at https://ai.azure.com",
            f"\n    Hint: Open '{azure_path!s}' in your editor to update your deployment details.",
            file=sys.stderr,
        )
        sys.exit(1)

    return models

@hookimpl
def register_models(register):
    azure_path = llm.user_dir() / "azure"
    azure_path.mkdir(exist_ok=True)
    azure_path = azure_path / "config.yaml"

    azure_models = get_azure_models(azure_path)

    for model in azure_models:
        if model.get('embedding_model'):
            continue

        aliases = model.pop("aliases", [])

        register(
            AzureChat(**model),
            AzureAsyncChat(**model),
            aliases=aliases,
        )


@hookimpl
def register_embedding_models(register):
    azure_path = llm.user_dir() / "azure"
    azure_path.mkdir(exist_ok=True)
    azure_path = azure_path / "config.yaml"

    azure_models = get_azure_models(azure_path)

    for model in azure_models:
        if not model.get('embedding_model'):
            continue

        aliases = model.pop("aliases", [])
        model.pop('embedding_model')

        register(
            AzureEmbedding(**model),
            aliases=aliases,
        )


class AzureShared(_Shared):
    needs_key = "azure"
    key_env_var = "AZURE_OPENAI_API_KEY"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_client(self, key, *, async_=False):
        kwargs = {
            "api_key": self.get_key(key),
            "api_version": self.api_version,
            "azure_endpoint": self.api_base,
        }
        if os.environ.get("LLM_OPENAI_SHOW_RESPONSES"):
            kwargs["http_client"] = self.logging_client()
        if async_:
            return AsyncAzureOpenAI(**kwargs)
        else:
            return AzureOpenAI(**kwargs)

    def build_kwargs(self, prompt, stream):
        kwargs = dict(not_nulls(prompt.options))
        json_object = kwargs.pop("json_object", None)
        if "max_tokens" not in kwargs and self.default_max_tokens is not None:
            kwargs["max_tokens"] = self.default_max_tokens
        if json_object:
            kwargs["response_format"] = {"type": "json_object"}
        # currently not supported for azure openai https://github.com/openai/openai-python/issues/1469
        # if stream:
        #     kwargs["stream_options"] = {"include_usage": True}
        return kwargs


class AzureChat(AzureShared, Chat):
    pass


class AzureAsyncChat(AzureShared, AsyncChat):
    pass


class AzureEmbedding(EmbeddingModel):
    needs_key = "azure"
    key_env_var = "AZURE_OPENAI_API_KEY"
    batch_size = 100

    def __init__(self, model_id, model_name, api_base, api_version):
        self.model_id = model_id
        self.model_name = model_name
        self.api_base = api_base
        self.api_version = api_version

    def embed_batch(self, items: Iterable[Union[str, bytes]]) -> Iterator[List[float]]:
        client = AzureOpenAI(
            api_key=self.get_key(),
            api_version=self.api_version,
            azure_endpoint=self.api_base,
        )
        kwargs = {
            "input": items,
            "model": self.model_name,
        }
        results = client.embeddings.create(**kwargs).data
        return ([float(r) for r in result.embedding] for result in results)
