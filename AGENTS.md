# AGENTS.md

This file provides guidance to coding agents when working with this repository.

## Overview

LLM plugin for Azure AI Foundry with **Entra ID authentication**. Supports Claude (via Anthropic SDK) and OpenAI-compatible models (GPT, Mistral, Llama via OpenAI SDK).

Key differentiator from Simon's built-in `extra-openai-models.yaml`: **Entra ID auth** instead of just API keys.

## Development Commands

```bash
pip install -e ".[anthropic]"            # Install with Anthropic support
pytest tests/test_capabilities.py        # Unit tests (no Azure creds needed)
pytest tests/test_capabilities.py::test_openai_supports_schema  # Single test
```

The project is also a uv package (`[tool.uv] package = true`, `pytest` in the `dev` dependency group), so `uv run pytest tests/test_capabilities.py` works without a manual install.

`tests/test_azure_anthropic.py` and `tests/test_azure_openai.py` are **integration tests**: they call `llm.get_model("claude-opus")` / `llm.get_model("azure-gpt4o")` and hit live Azure, so they require `az login` plus those exact `model_id`s in your config. Run them directly (`python tests/test_azure_openai.py`), not in CI. `tests/test_capabilities.py` is the only suite that runs offline — it constructs the model classes directly and asserts on `attachment_types`, `supports_schema`, and `supports_tools`.

There is no CI test workflow; `.github/workflows/publish.yml` only builds and publishes.

## Release Process

1. Update version in `pyproject.toml`
2. Commit: `git commit -m "Bump version to X.Y"`
3. Tag and push: `git tag X.Y && git push origin main X.Y`
4. Create GitHub release: `gh release create X.Y --title "X.Y" --generate-notes`
5. PyPI publish happens automatically via `.github/workflows/publish.yml`

## Architecture

### Package Structure

```
llm_azure/
  __init__.py    # register_models hook, config loading, provider dispatch
  anthropic.py   # AzureAnthropicChat (Claude)
  openai.py      # AzureOpenAIShared + AzureOpenAIChat (GPT, Mistral, DeepSeek, Llama)
tests/
  test_capabilities.py     # offline unit tests
  test_azure_anthropic.py  # live integration tests
  test_azure_openai.py     # live integration tests
```

The core pattern: each provider class **subclasses LLM's existing model class** and only overrides client construction to inject Azure auth. The bulk of request/response handling is inherited.

- `AzureOpenAIChat(AzureOpenAIShared, Chat)`, where `AzureOpenAIShared` subclasses `_Shared` from `llm.default_plugins.openai_models` — overrides `get_client()` only. The constructor passes `vision=True`, `supports_schema=True`, `supports_tools=True` to the parent.
- `AzureAnthropicChat(ClaudeMessages)` from `llm_anthropic` — overrides `execute()` to use `AnthropicFoundry` (built in `_get_azure_client()`) instead of the standard Anthropic client, while reusing the parent's `build_kwargs`, `prefill_text`, and `add_tool_usage`. Note it must re-set `self.model_id` after `super().__init__()` because the parent prepends an `"anthropic/"` prefix.
- Both classes set a `model_type` string (`"Azure Anthropic"` / `"Azure OpenAI Chat"`) and a matching `__str__`, so `llm models` shows the Azure prefix.

`register_models` (in `__init__.py`) reads the config, pops `aliases` off each entry, and dispatches on the `provider` field; unknown providers are silently skipped. A missing config file yields an empty model list rather than an error.

### Providers

| Provider | SDK class | Auth | Models |
|----------|-----------|------|--------|
| `anthropic` | `anthropic.AnthropicFoundry` | Entra ID / API key | Claude |
| `openai` | `openai.OpenAI` / `AsyncOpenAI` | Entra ID / API key | GPT, Mistral, DeepSeek, Llama |

### Configuration

Models defined in `azure/config.yaml` under `llm.user_dir()`, which is `click.get_app_dir("io.datasette.llm")` — platform-specific: `~/Library/Application Support/io.datasette.llm` on macOS, `~/.config/io.datasette.llm` on Linux (override with `LLM_USER_PATH`). Resolve it with `dirname "$(llm logs path)"`:

```yaml
- model_id: claude-opus
  provider: anthropic
  model_name: claude-opus-4-5
  endpoint: https://RESOURCE.openai.azure.com/anthropic/
  aliases: [opus]
  # api_key_name: azure  # Optional, uses Entra ID if omitted

- model_id: azure-gpt4o
  provider: openai
  model_name: gpt-4o
  endpoint: https://RESOURCE.openai.azure.com/openai/v1/
  aliases: [agpt]
```

### Authentication Flow

1. If `api_key_name` is set → use stored API key via `llm keys`
2. Otherwise → use `DefaultAzureCredential` (Entra ID)
   - Requires `az login` and "Cognitive Services User" role

### Key Implementation Details

- Lazy imports: Provider SDKs (`anthropic`, `openai`, `azure.identity`) only imported when that provider/auth path is used
- Token provider: For Entra ID, uses `get_bearer_token_provider()` with scope `https://cognitiveservices.azure.com/.default`. OpenAI passes the resolved token as `api_key=token_provider()`; Anthropic passes `azure_ad_token_provider=token_provider`
- When `api_key_name` is set, `needs_key`/`key_env_var` (`LLM_<NAME>_KEY`) are populated so LLM resolves the key via `llm keys`; otherwise both stay `None` and Entra ID is used
- Endpoint suffix matters: Anthropic endpoints end in `/anthropic/` (uses `/v1/messages`), OpenAI-compatible endpoints (including Mistral) end in `/openai/v1/`
