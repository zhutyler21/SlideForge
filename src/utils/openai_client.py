"""统一的 OpenAI 客户端工厂"""

from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, RateLimitError

load_dotenv()


def create_client() -> OpenAI:
    """创建统一的 OpenAI 客户端，读取 .env 配置"""
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("BASE_URL"),
    )


def get_model(purpose: str) -> str:
    """
    根据用途获取对应的模型名称

    Args:
        purpose: "image" | "prompt" | "outline" | "vision"

    Returns:
        模型名称字符串

    Raises:
        ValueError: 当环境变量未设置时
    """
    mapping = {
        "image": "IMAGE_GEN_MODEL",
        "prompt": "PROMPT_GEN_MODEL",
        "outline": "OUTLINE_GEN_MODEL",
        "vision": "VISION_MODEL",
    }
    env_var = mapping.get(purpose)
    if not env_var:
        raise ValueError(f"未知的模型用途: {purpose}，支持: {list(mapping.keys())}")

    model = os.getenv(env_var)
    if not model:
        raise ValueError(f"环境变量 {env_var} 未设置，请检查 .env 文件")
    return model


def chat_with_retry(
    client: OpenAI,
    max_retries: int = 3,
    **kwargs: Any,
) -> Any:
    """
    带重试的 chat.completions.create 封装

    失败时使用指数退避重试，适用于网络超时、速率限制、服务端临时错误等场景。

    Args:
        client: OpenAI 客户端
        max_retries: 最大重试次数（默认 3）
        **kwargs: 传递给 client.chat.completions.create 的所有参数

    Returns:
        API 响应对象
    """
    retryable_errors = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except retryable_errors as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  API 调用失败 ({attempt + 1}/{max_retries}): {str(e)[:80]}，{wait}s 后重试")
                time.sleep(wait)
            else:
                raise
