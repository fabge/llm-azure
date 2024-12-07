from typing import Iterable, Iterator, List, Union, Optional
from pathlib import Path

import llm
import yaml
from llm import EmbeddingModel, hookimpl, Prompt, Response, Model
from llm.default_plugins.openai_models import Chat, combine_chunks
from llm.utils import remove_dict_none_values
from openai import AzureOpenAI


@hookimpl
def register_models(register):
    azure_path = config_dir() / "config.yaml"
    if not azure_path.exists():
        return
    with open(azure_path) as f:
        azure_models = yaml.safe_load(f)
    for model in azure_models or []:
        if not model.get("embedding_model"):
            model_id = model["model_id"]
            model_name = model["deployment_name"]
            can_stream = model.get("can_stream", True)
            endpoint = model["endpoint"]
            api_version = model["api_version"]
            aliases = model.get("aliases", [])
            attachment_types = model.get("attachment_types")
            register(
                AzureChat(
                    model_id,
                    model_name,
                    can_stream,
                    endpoint,
                    api_version,
                    attachment_types,
                ),
                aliases=aliases,
            )


@hookimpl
def register_embedding_models(register):
    azure_path = config_dir() / "config.yaml"
    if not azure_path.exists():
        return
    with open(azure_path) as f:
        azure_models = yaml.safe_load(f)
    for model in azure_models or []:
        if model.get("embedding_model"):
            model_id = model["model_id"]
            model_name = model["deployment_name"]
            endpoint = model["endpoint"]
            api_version = model["api_version"]
            aliases = model.get("aliases", [])
            register(
                AzureEmbedding(model_id, model_name, endpoint, api_version),
                aliases=aliases,
            )


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

    def __init__(
        self,
        model_id,
        model_name,
        can_stream,
        endpoint,
        api_version,
        attachment_types=None,
    ):
        self.model_id = model_id
        self.model_name = model_name
        self.can_stream = can_stream
        self.endpoint = endpoint
        self.api_version = api_version
        self.attachment_types = attachment_types or set()

    def get_client(self):
        return _get_client(self)

    def __str__(self):
        return "AzureOpenAI Chat: {}".format(self.model_id)

    def execute(self, prompt, stream, response, conversation=None):
        messages = []
        current_system = None

        # Handle conversation history and attachments
        if conversation is not None:
            for prev_response in conversation.responses:
                if prev_response.attachments:
                    attachment_message = []
                    if prev_response.prompt.prompt:
                        attachment_message.append(
                            {"type": "text", "text": prev_response.prompt.prompt}
                        )
                    for attachment in prev_response.attachments:
                        attachment_message.append(_attachment(attachment))
                    messages.append({"role": "user", "content": attachment_message})
                else:
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

                messages.append(
                    {"role": "assistant", "content": prev_response.text_or_raise()}
                )

        # Handle system prompt
        if prompt.system and prompt.system != current_system:
            messages.append({"role": "system", "content": prompt.system})

        # Handle attachments for current prompt
        if not prompt.attachments:
            messages.append({"role": "user", "content": prompt.prompt})
        else:
            attachment_message = []
            if prompt.prompt:
                attachment_message.append({"type": "text", "text": prompt.prompt})
            for attachment in prompt.attachments:
                attachment_message.append(_attachment(attachment))
            messages.append({"role": "user", "content": attachment_message})

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
            response.response_json = remove_dict_none_values(completion.model_dump())
            yield completion.choices[0].message.content


def config_dir():
    dir_path = llm.user_dir() / "azure"
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def _get_client(self):
    return AzureOpenAI(
        api_key=self.key,
        api_version=self.api_version,
        azure_endpoint=self.endpoint,
    )


def _attachment(attachment):
    url = attachment.url
    base64_content = ""
    if not url or attachment.resolve_type().startswith("audio/"):
        base64_content = attachment.base64_content()
        url = f"data:{attachment.resolve_type()};base64,{base64_content}"
    if attachment.resolve_type().startswith("image/"):
        return {"type": "image_url", "image_url": {"url": url}}
    else:
        format_ = "wav" if attachment.resolve_type() == "audio/wav" else "mp3"
        return {
            "type": "input_audio",
            "input_audio": {
                "data": base64_content,
                "format": format_,
            },
        }
