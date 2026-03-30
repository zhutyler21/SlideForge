#!/usr/bin/env python3
"""
配置验证工具

在脚本启动时验证必需的环境变量和配置
"""

from __future__ import annotations

import os
import sys
from typing import Any


class ConfigError(Exception):
    """配置错误异常"""

    pass


def validate_env_vars(required_vars: list[str]) -> dict[str, str]:
    """
    验证必需的环境变量是否存在

    Args:
        required_vars: 必需的环境变量名称列表

    Returns:
        环境变量字典

    Raises:
        ConfigError: 当缺少必需的环境变量时
    """
    missing = []
    config = {}

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            config[var] = value

    if missing:
        raise ConfigError(
            f"缺少必需的环境变量: {', '.join(missing)}\n"
            f"请在 .env 文件中配置这些变量，参考 .env.example"
        )

    return config


def validate_openai_config() -> dict[str, str]:
    """
    验证 OpenAI 相关配置

    Returns:
        配置字典，包含 api_key, base_url, model

    Raises:
        ConfigError: 当配置不完整时
    """
    return validate_env_vars(["OPENAI_API_KEY", "BASE_URL", "IMAGE_GEN_MODEL"])


def validate_prompt_gen_config() -> dict[str, str]:
    """
    验证提示词生成相关配置

    Returns:
        配置字典，包含 api_key, base_url, gen_prompt_model

    Raises:
        ConfigError: 当配置不完整时
    """
    return validate_env_vars(["OPENAI_API_KEY", "BASE_URL", "PROMPT_GEN_MODEL"])


def validate_outline_config() -> dict[str, str]:
    """
    验证大纲生成相关配置

    Returns:
        配置字典，包含 api_key, base_url, gen_outline_model

    Raises:
        ConfigError: 当配置不完整时
    """
    return validate_env_vars(["OPENAI_API_KEY", "BASE_URL", "OUTLINE_GEN_MODEL"])


def validate_vision_config() -> dict[str, str]:
    """
    验证多模态视觉分析相关配置

    Returns:
        配置字典，包含 api_key, base_url, vision_model

    Raises:
        ConfigError: 当配置不完整时
    """
    return validate_env_vars(["OPENAI_API_KEY", "BASE_URL", "VISION_MODEL"])


def validate_full_config() -> dict[str, str]:
    """
    验证所有配置项

    Returns:
        完整配置字典

    Raises:
        ConfigError: 当配置不完整时
    """
    return validate_env_vars([
        "OPENAI_API_KEY", "BASE_URL",
        "IMAGE_GEN_MODEL", "PROMPT_GEN_MODEL",
        "OUTLINE_GEN_MODEL", "VISION_MODEL",
    ])
