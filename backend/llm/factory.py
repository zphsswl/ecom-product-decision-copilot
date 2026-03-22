from os import getenv

from llm.providers import (
    BaseLLMProvider,
    DeepSeekProvider,
    DoubaoProvider,
    OpenAIProvider,
)


def get_llm_provider(provider: str | None = None) -> BaseLLMProvider:
    """
    根据 provider 名称返回对应的 LLM provider。
    优先级：
    1. 显式传入 provider
    2. .env 里的 LLM_PROVIDER
    3. 默认 deepseek
    """
    selected = (provider or getenv("LLM_PROVIDER") or "deepseek").lower()

    if selected == "deepseek":
        return DeepSeekProvider()

    if selected == "doubao":
        return DoubaoProvider()

    if selected == "openai":
        return OpenAIProvider()

    raise ValueError(f"Unsupported provider: {selected}")