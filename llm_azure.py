from typing import Iterable, Iterator, List, Union

import llm
import yaml
from llm import EmbeddingModel, hookimpl
from llm.default_plugins.openai_models import Chat, combine_chunks
from llm.utils import remove_dict_none_values
from openai import AzureOpenAI


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
            vision = model.get("vision", False)
            audio = model.get("audio", False)
            reasoning = model.get("reasoning", False)
            allows_system_prompt = model.get("allows_system_prompt", True)
            register(
                AzureChat(
                    model_id,
                    model_name,
                    can_stream,
                    endpoint,
                    api_version,
                    vision=vision,
                    audio=audio,
                    reasoning=reasoning,
                    allows_system_prompt=allows_system_prompt
                ),
                aliases=aliases
            )


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
            register(AzureEmbedding(model_id, model_name, endpoint, api_version), aliases=aliases)


class AzureEmbedding(EmbeddingModel):
    needs_key = "azure"
    key_env_var = "AZURE_OPENAI_API_KEY"
    batch_size = 100

    def __init__(self, model_id, model_name, endpoint, api_version):
        self.model_id = model_id
        self.model_name = model_name
        self.endpoint = endpoint
        self.api_version = api_version

    def embed_batch(self, items: Iterable[Union[str, bytes]]) -> Iterator[List[float]]:
        kwargs = {
            "input": items,
            "model": self.model_name,
        }
        client = _get_client(self)
        results = client.embeddings.create(**kwargs).data
        return ([float(r) for r in result.embedding] for result in results)


class AzureChat(Chat):
    needs_key = "azure"
    key_env_var = "AZURE_OPENAI_API_KEY"

    def __init__(self, model_id, model_name, can_stream, endpoint, api_version, vision=False, audio=False, reasoning=False, allows_system_prompt=True):
        super().__init__(
            model_id,
            model_name=model_name,
            can_stream=can_stream,
            vision=vision,
            audio=audio,
            reasoning=reasoning,
            allows_system_prompt=allows_system_prompt
        )
        self.endpoint = endpoint
        self.api_version = api_version

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
        api_key=self.key,
        api_version=self.api_version,
        azure_endpoint=self.endpoint,
    )
