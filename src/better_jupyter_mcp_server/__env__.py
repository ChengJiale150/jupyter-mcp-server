"""
统一配置管理模块
Unified Configuration Management Module

该模块负责加载和管理所有配置项，提供统一的配置访问接口
支持环境变量优先原则：如果存在同名环境变量，则优先使用环境变量的值
This module is responsible for loading and managing all configuration items, providing a unified configuration access interface
Supports environment variable priority: if an environment variable with the same name exists, use the environment variable value first
"""

import os
import tomllib
from pathlib import Path
from typing import Any, Dict, Union

# 获取配置文件路径
# Get configuration file path
_config_path = Path(__file__).parent / "config.toml"

# 加载配置
# Load configuration
with open(_config_path, "rb") as f:
    _config = tomllib.load(f)

def _get_env_bool(env_name: str, default_value: bool) -> bool:
    """
    从环境变量获取布尔值，支持多种格式
    Get boolean value from environment variable, supporting multiple formats
    
    Args:
        env_name: 环境变量名 / Environment variable name
        default_value: 默认值 / Default value
        
    Returns:
        bool: 布尔值 / Boolean value
    """
    env_value = os.getenv(env_name)
    if env_value is None:
        return default_value
    
    # 支持的真值格式 / Supported true value formats
    true_values = {'true', '1', 'yes', 'on', 'enable', 'enabled'}
    # 支持的假值格式 / Supported false value formats  
    false_values = {'false', '0', 'no', 'off', 'disable', 'disabled'}
    
    env_value_lower = env_value.lower().strip()
    
    if env_value_lower in true_values:
        return True
    elif env_value_lower in false_values:
        return False
    else:
        print(f"Warning: Invalid boolean value '{env_value}' for {env_name}, using default: {default_value}")
        return default_value

def _get_env_int(env_name: str, default_value: int) -> int:
    """
    从环境变量获取整数值
    Get integer value from environment variable
    
    Args:
        env_name: 环境变量名 / Environment variable name
        default_value: 默认值 / Default value
        
    Returns:
        int: 整数值 / Integer value
    """
    env_value = os.getenv(env_name)
    if env_value is None:
        return default_value
    
    try:
        return int(env_value.strip())
    except ValueError:
        print(f"Warning: Invalid integer value '{env_value}' for {env_name}, using default: {default_value}")
        return default_value

# 基础配置 / Basic Configuration
# 环境变量优先，如果没有环境变量则使用配置文件的值
# Environment variables take priority, use config file values if no environment variables
ALLOW_IMG: bool = _get_env_bool("ALLOW_IMG", _config["basic"]["ALLOW_IMG"])
ALLOW_IMG_PREPROCESS: bool = _get_env_bool("ALLOW_IMG_PREPROCESS", _config["basic"]["ALLOW_IMG_PREPROCESS"])
FORCE_SYNC: bool = _get_env_bool("FORCE_SYNC", _config["basic"]["FORCE_SYNC"])

# 图片配置 / Image Configuration
MAX_WIDTH: int = _get_env_int("MAX_WIDTH", _config["img"]["MAX_WIDTH"])
MAX_HEIGHT: int = _get_env_int("MAX_HEIGHT", _config["img"]["MAX_HEIGHT"])
IMAGE_TOEKN_SIZE: int = _get_env_int("IMAGE_TOEKN_SIZE", _config["img"]["IMAGE_TOEKN_SIZE"])
