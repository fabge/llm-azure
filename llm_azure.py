from typing import Iterable, Iterator, List, Union

import llm
import yaml
from llm import EmbeddingModel, hookimpl
from llm.default_plugins.openai_models import Chat, combine_chunks
from llm.utils import remove_dict_none_values
from openai import AzureOpenAI

DEFAULT_KEY_ALIAS = "azure"
DEFAULT_KEY_ENV_VAR = "AZURE_OPENAI_API_KEY"

@hookimpl
def register_models(register):
    azure_path = config_dir() / "config.yaml"
    with open(azure_path) as f:
        azure_models = yaml.safe_load(f)
    for model in azure_models:
        if not model.get('embedding_model'):
            model_id = model["model_id"]
            model_name = model["deployment_name"]
            can_stream = model.get("can_stream", True)
            endpoint = model["endpoint"]
            api_version = model["api_version"]
            aliases = model.get("aliases", [])
            needs_key = model.get("needs_key", DEFAULT_KEY_ALIAS)
            key_env_var = model.get("key_env_var", DEFAULT_KEY_ENV_VAR)
            register(AzureChat(model_id, model_name, can_stream, endpoint, api_version, needs_key, key_env_var), aliases=aliases)


@hookimpl
def register_embedding_models(register):
    azure_path = config_dir() / "config.yaml"
    with open(azure_path) as f:
        azure_models = yaml.safe_load(f)
    for model in azure_models:
        if model.get('embedding_model'):
            model_id = model["model_id"]
            model_name = model["deployment_name"]
            endpoint = model["endpoint"]
            api_version = model["api_version"]
            aliases = model.get("aliases", [])
            needs_key = model.get("needs_key", DEFAULT_KEY_ALIAS)
            key_env_var = model.get("key_env_var", DEFAULT_KEY_ENV_VAR)
            register(AzureEmbedding(model_id, model_name, endpoint, api_version, needs_key, key_env_var)
, aliases=aliases)


class AzureEmbedding(EmbeddingModel):
    needs_key = DEFAULT_KEY_ALIAS
    key_env_var = DEFAULT_KEY_ENV_VAR
    batch_size = 100

    def __init__(self, model_id, model_name, endpoint, api_version, needs_key=DEFAULT_KEY_ALIAS, key_env_var=DEFAULT_KEY_ENV_VAR):
        self.model_id = model_id
        self.model_name = model_name
        self.endpoint = endpoint
        self.api_version = api_version
        self.needs_key = needs_key
        self.key_env_var = key_env_var

    def embed_batch(self, items: Iterable[Union[str, bytes]]) -> Iterator[List[float]]:
        kwargs = {
            "input": items,
            "model": self.model_name,
        }
        client = _get_client(self)
        results = client.embeddings.create(**kwargs).data
        return ([float(r) for r in result.embedding] for result in results)


class AzureChat(Chat):
    needs_key = DEFAULT_KEY_ALIAS
    key_env_var = DEFAULT_KEY_ENV_VAR

    def __init__(self, model_id, model_name, can_stream, endpoint, api_version, needs_key = DEFAULT_KEY_ALIAS, key_env_var= DEFAULT_KEY_ENV_VAR):
        self.model_id = model_id
        self.model_name = model_name
        self.can_stream = can_stream
        self.endpoint = endpoint
        self.api_version = api_version
        self.needs_key = needs_key
        self.key_env_var = key_env_var

    def get_client(self):
        return _get_client(self)

    def __str__(self):
        return "AzureOpenAI Chat: {}".format(self.model_id)

    def execute(self, prompt, stream, response, conversation=None):
        messages = []
        current_system = None
        if conversation is not None:
            for prev_response in conversation.responses:
                if (
                    prev_response.prompt.system
                    and prev_response.prompt.system != current_system
                ):
                    messages.append(
                        {"role": "system", "content": prev_response.prompt.system},
                    )
                    current_system = prev_response.prompt.system
                messages.append(
                    {"role": "user", "content": prev_response.prompt.prompt},
                )
                messages.append({"role": "assistant", "content": prev_response.text()})
        if prompt.system and prompt.system != current_system:
            messages.append({"role": "system", "content": prompt.system})
        messages.append({"role": "user", "content": prompt.prompt})
        response._prompt_json = {"messages": messages}
        kwargs = self.build_kwargs(prompt, stream)
        client = self.get_client()
        if stream:
            completion = client.chat.completions.create(
                model=self.model_name or self.model_id,
                messages=messages,
                stream=True,
                **kwargs,
            )
            chunks = []
            for chunk in completion:
                chunks.append(chunk)
                if chunk.choices:
                    try:
                        content = chunk.choices[0].delta.content
                    except IndexError:
                        content = None
                    if content is not None:
                        yield content
            response.response_json = remove_dict_none_values(combine_chunks(chunks))
        else:
            completion = client.chat.completions.create(
                model=self.model_name or self.model_id,
                messages=messages,
                stream=False,
                **kwargs,
            )
            response.response_json = remove_dict_none_values(completion.dict())
            yield completion.choices[0].message.content


def config_dir():
    dir_path = llm.user_dir() / "azure"
    if not dir_path.exists():
        dir_path.mkdir()
    return dir_path


def _get_client(self):
    
    return AzureOpenAI(
        api_key=self.get_key(),
        api_version=self.api_version,
        azure_endpoint=self.endpoint,
    )
