import os
import traceback

from langchain.chat_models import BaseChatModel, init_chat_model
from pydantic import SecretStr

from src import config
from src.utils import get_docker_safe_url
from src.utils.logging_config import logger


def _patch_langchain_openai_reasoning_mapping() -> None:
    """Patch langchain_openai to preserve reasoning fields from OpenAI-compatible responses."""
    try:
        import langchain_openai.chat_models.base as lc_openai_base
    except Exception:
        return

    if getattr(lc_openai_base, "_yuxi_reasoning_patch_applied", False):
        return

    original_convert_dict = lc_openai_base._convert_dict_to_message
    original_convert_delta = lc_openai_base._convert_delta_to_message_chunk

    def _extract_reasoning(payload: dict) -> str:
        if not isinstance(payload, dict):
            return ""
        provider_specific_fields = payload.get("provider_specific_fields")
        return (
            payload.get("reasoning_content")
            or payload.get("reasoning")
            or ((provider_specific_fields or {}).get("reasoning_content") if isinstance(provider_specific_fields, dict) else "")
            or ((provider_specific_fields or {}).get("reasoning") if isinstance(provider_specific_fields, dict) else "")
            or ""
        )

    def _convert_dict_to_message_with_reasoning(_dict):
        message = original_convert_dict(_dict)
        reasoning = _extract_reasoning(dict(_dict) if _dict is not None else {})
        if reasoning and hasattr(message, "additional_kwargs") and isinstance(message.additional_kwargs, dict):
            message.additional_kwargs["reasoning_content"] = (
                message.additional_kwargs.get("reasoning_content") or reasoning
            )
        return message

    def _convert_delta_to_message_chunk_with_reasoning(_dict, default_class):
        chunk = original_convert_delta(_dict, default_class)
        reasoning = _extract_reasoning(dict(_dict) if _dict is not None else {})
        if reasoning and hasattr(chunk, "additional_kwargs") and isinstance(chunk.additional_kwargs, dict):
            existing = chunk.additional_kwargs.get("reasoning_content", "")
            chunk.additional_kwargs["reasoning_content"] = f"{existing}{reasoning}" if existing else reasoning
        return chunk

    lc_openai_base._convert_dict_to_message = _convert_dict_to_message_with_reasoning
    lc_openai_base._convert_delta_to_message_chunk = _convert_delta_to_message_chunk_with_reasoning
    lc_openai_base._yuxi_reasoning_patch_applied = True
    logger.info("Applied langchain_openai reasoning mapping patch")


def load_chat_model(fully_specified_name: str, **kwargs) -> BaseChatModel:
    """
    Load a chat model from a fully specified name.
    """
    provider, model = fully_specified_name.split("/", maxsplit=1)

    assert provider != "custom", "[弃用] 自定义模型已移除，请在 src/config/static/models.py 中配置"

    model_info = config.model_names.get(provider)
    if not model_info:
        raise ValueError(f"Unknown model provider: {provider}")

    env_var = model_info.env

    api_key = os.getenv(env_var) or env_var

    base_url = get_docker_safe_url(model_info.base_url)
    # Keep the agent call chain streaming by default.
    kwargs.setdefault("streaming", True)
    if provider == "vllm-local":
        extra_body = kwargs.get("extra_body") or {}
        if "priority" not in extra_body:
            extra_body["priority"] = 0
        kwargs["extra_body"] = extra_body

    if provider in ["openai", "deepseek"]:
        _patch_langchain_openai_reasoning_mapping()
        model_spec = f"{provider}:{model}"
        logger.debug(f"[offical] Loading model {model_spec} with kwargs {kwargs}")
        return init_chat_model(model_spec, **kwargs)

    elif provider in ["dashscope"]:
        from langchain_deepseek import ChatDeepSeek

        return ChatDeepSeek(
            model=model,
            api_key=SecretStr(api_key),
            base_url=base_url,
            api_base=base_url,
            stream_usage=True,
            **kwargs,
        )

    else:
        try:  # 其他模型，默认使用OpenAIBase, like openai, zhipuai
            from langchain_openai import ChatOpenAI

            _patch_langchain_openai_reasoning_mapping()
            return ChatOpenAI(
                model=model,
                api_key=SecretStr(api_key),
                base_url=base_url,
                stream_usage=True,
                **kwargs,
            )
        except Exception as e:
            raise ValueError(f"Model provider {provider} load failed, {e} \n {traceback.format_exc()}")
