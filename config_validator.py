#!/usr/bin/env python3
"""
配置验证模块

提供配置 Schema 定义、验证和启动时完整性检查功能。
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class ValidationError:
    """配置验证错误"""
    field: str
    message: str
    severity: str  # 'error' | 'warning'


# 配置 Schema 定义
CONFIG_SCHEMA = {
    "version": {
        "type": "string",
        "required": True,
        "pattern": r"^\d+\.\d+\.\d+$",
        "description": "配置文件版本"
    },
    "api": {
        "type": "object",
        "required": True,
        "properties": {
            "dashscope_api_key": {
                "type": "string",
                "required": True,
                "min_length": 1,
                "description": "阿里云 DashScope API 密钥"
            },
            "embedding_model": {
                "type": "string",
                "required": False,
                "default": "text-embedding-v4",
                "description": "Embedding 模型名称"
            },
            "dimension": {
                "type": "integer",
                "required": False,
                "default": 1024,
                "min": 1,
                "max": 4096,
                "description": "向量维度"
            }
        }
    },
    "qiniu": {
        "type": "object",
        "required": False,
        "properties": {
            "access_key": {
                "type": "string",
                "required": False,
                "description": "七牛云 Access Key"
            },
            "secret_key": {
                "type": "string",
                "required": False,
                "description": "七牛云 Secret Key"
            },
            "bucket": {
                "type": "string",
                "required": False,
                "description": "七牛云存储桶名称"
            },
            "domain": {
                "type": "string",
                "required": False,
                "description": "七牛云 CDN 域名"
            },
            "default_expiry_days": {
                "type": "integer",
                "required": False,
                "default": 7,
                "min": 1,
                "max": 365,
                "description": "默认有效期（天）"
            }
        }
    },
    "directories": {
        "type": "object",
        "required": True,
        "properties": {
            "inbox": {
                "type": "string",
                "required": True,
                "description": "收件箱目录"
            },
            "archive": {
                "type": "string",
                "required": True,
                "description": "归档目录"
            },
            "temp": {
                "type": "string",
                "required": True,
                "description": "临时目录"
            }
        }
    },
    "storage_policy": {
        "type": "object",
        "required": True,
        "properties": {
            "hot_extensions": {
                "type": "array",
                "required": True,
                "item_type": "string",
                "description": "热文件扩展名列表"
            },
            "cold_extensions": {
                "type": "array",
                "required": True,
                "item_type": "string",
                "description": "冷文件扩展名列表"
            },
            "warm_extensions": {
                "type": "array",
                "required": True,
                "item_type": "string",
                "description": "温文件扩展名列表"
            }
        }
    },
    "features": {
        "type": "object",
        "required": False,
        "properties": {
            "enable_semantic_search": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "启用语义搜索"
            },
            "enable_auto_upload": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "启用自动上传"
            },
            "enable_duplicate_check": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "启用重复检查"
            },
            "enable_version_control": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "启用版本控制"
            }
        }
    }
}


class ConfigValidator:
    """配置验证器"""

    def __init__(self, schema: Dict = None):
        """
        初始化验证器

        Args:
            schema: 验证 Schema，默认使用 CONFIG_SCHEMA
        """
        self.schema = schema or CONFIG_SCHEMA
        self.errors: List[ValidationError] = []

    def validate(self, config: Dict) -> Tuple[bool, List[ValidationError]]:
        """
        验证配置

        Args:
            config: 待验证的配置字典

        Returns:
            (是否通过验证，错误列表)
        """
        self.errors = []
        self._validate_schema(config, self.schema, "")
        return len(self.errors) == 0, self.errors

    def _validate_schema(self, config: Any, schema: Dict, path: str) -> None:
        """递归验证 Schema"""
        schema_type = schema.get("type")

        # 类型检查
        if schema_type == "object":
            if not isinstance(config, dict):
                self._add_error(path, f"期望对象类型，得到 {type(config).__name__}")
                return

            # 验证必需字段
            properties = schema.get("properties", {})
            for field_name, field_schema in properties.items():
                field_path = f"{path}.{field_name}" if path else field_name
                field_value = config.get(field_name)

                if field_schema.get("required", False) and field_value is None:
                    self._add_error(field_path, f"字段是必需的", "error")
                elif field_value is not None:
                    self._validate_schema(field_value, field_schema, field_path)

        elif schema_type == "string":
            if not isinstance(config, str):
                self._add_error(path, f"期望字符串类型，得到 {type(config).__name__}")
                return

            # 最小长度检查
            min_length = schema.get("min_length")
            if min_length is not None and len(config) < min_length:
                self._add_error(path, f"字符串长度不能小于 {min_length}")

            # 正则表达式检查
            pattern = schema.get("pattern")
            if pattern:
                import re
                if not re.match(pattern, config):
                    self._add_error(path, f"字符串不匹配模式：{pattern}")

        elif schema_type == "integer":
            if not isinstance(config, int):
                self._add_error(path, f"期望整数类型，得到 {type(config).__name__}")
                return

            # 范围检查
            min_val = schema.get("min")
            max_val = schema.get("max")
            if min_val is not None and config < min_val:
                self._add_error(path, f"值不能小于 {min_val}")
            if max_val is not None and config > max_val:
                self._add_error(path, f"值不能大于 {max_val}")

        elif schema_type == "boolean":
            if not isinstance(config, bool):
                self._add_error(path, f"期望布尔类型，得到 {type(config).__name__}")

        elif schema_type == "array":
            if not isinstance(config, list):
                self._add_error(path, f"期望数组类型，得到 {type(config).__name__}")
                return

            # 检查数组项类型
            item_type = schema.get("item_type")
            if item_type:
                for i, item in enumerate(config):
                    item_path = f"{path}[{i}]"
                    if item_type == "string" and not isinstance(item, str):
                        self._add_error(item_path, f"期望字符串类型，得到 {type(item).__name__}")
                    elif item_type == "integer" and not isinstance(item, int):
                        self._add_error(item_path, f"期望整数类型，得到 {type(item).__name__}")

    def _add_error(self, field: str, message: str, severity: str = "error") -> None:
        """添加验证错误"""
        self.errors.append(ValidationError(field=field, message=message, severity=severity))


def validate_config(config: Dict) -> Tuple[bool, List[ValidationError]]:
    """
    验证配置完整性

    Args:
        config: 配置字典

    Returns:
        (是否通过验证，错误列表)
    """
    validator = ConfigValidator()
    return validator.validate(config)


def check_config_integrity(config_path: Path) -> Tuple[bool, str, List[ValidationError]]:
    """
    检查配置文件完整性

    Args:
        config_path: 配置文件路径

    Returns:
        (是否通过验证，消息，错误列表)
    """
    if not config_path.exists():
        return False, f"配置文件不存在：{config_path}", []

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"配置文件解析错误：{e}", []

    is_valid, errors = validate_config(config)

    if is_valid:
        return True, "配置验证通过", []
    else:
        error_messages = [f"{e.field}: {e.message}" for e in errors if e.severity == "error"]
        warning_messages = [f"{e.field}: {e.message}" for e in errors if e.severity == "warning"]

        messages = []
        if error_messages:
            messages.append(f"错误 ({len(error_messages)}): {'; '.join(error_messages)}")
        if warning_messages:
            messages.append(f"警告 ({len(warning_messages)}): {'; '.join(warning_messages)}")

        return False, "; ".join(messages), errors


def check_api_config(config: Dict) -> Tuple[bool, str]:
    """
    检查 API 配置

    Args:
        config: 配置字典

    Returns:
        (是否通过验证，消息)
    """
    api_config = config.get("api", {})
    api_key = api_config.get("dashscope_api_key", "")

    # 检查环境变量
    if not api_key:
        api_key = os.getenv("DASHSCOPE_API_KEY", "")

    if not api_key or api_key == "YOUR_DASHSCOPE_API_KEY_HERE":
        return False, "阿里云 DashScope API Key 未配置"

    return True, "API 配置有效"


def check_qiniu_config(config: Dict) -> Tuple[bool, str]:
    """
    检查七牛云配置

    Args:
        config: 配置字典

    Returns:
        (是否通过验证，消息)
    """
    qiniu_config = config.get("qiniu", {})

    if not qiniu_config:
        return True, "七牛云配置未设置（可选）"

    access_key = qiniu_config.get("access_key", "")
    secret_key = qiniu_config.get("secret_key", "")
    bucket = qiniu_config.get("bucket", "")
    domain = qiniu_config.get("domain", "")

    # 检查是否填写了占位符
    if access_key == "YOUR_QINIU_ACCESS_KEY_HERE":
        return False, "七牛云 Access Key 未配置"
    if secret_key == "YOUR_QINIU_SECRET_KEY_HERE":
        return False, "七牛云 Secret Key 未配置"

    # 如果配置了密钥，检查其他字段
    if access_key and secret_key:
        if not bucket:
            return False, "七牛云存储桶名称未配置"
        if not domain:
            return False, "七牛云 CDN 域名未配置"

    return True, "七牛云配置有效"


def print_config_status(config: Dict) -> None:
    """
    打印配置状态

    Args:
        config: 配置字典
    """
    print("\n📋 配置状态检查")
    print("=" * 50)

    # API 配置
    api_valid, api_msg = check_api_config(config)
    api_status = "✅" if api_valid else "❌"
    print(f"{api_status} API 配置：{api_msg}")

    # 七牛云配置
    qiniu_valid, qiniu_msg = check_qiniu_config(config)
    qiniu_status = "✅" if qiniu_valid else "⚠️"
    print(f"{qiniu_status} 七牛云配置：{qiniu_msg}")

    # 完整验证
    is_valid, errors = validate_config(config)

    if errors:
        print(f"\n验证问题 ({len(errors)}):")
        for error in errors:
            severity_icon = "❌" if error.severity == "error" else "⚠️"
            print(f"  {severity_icon} {error.field}: {error.message}")
    else:
        print("\n✅ 所有配置验证通过")

    print("=" * 50)


# CLI
if __name__ == "__main__":
    import sys

    config_file = Path("config/config.json")
    if len(sys.argv) > 1:
        config_file = Path(sys.argv[1])

    print(f"检查配置文件：{config_file}")

    is_valid, message, errors = check_config_integrity(config_file)

    if is_valid:
        print(f"✅ {message}")

        # 加载并显示详细状态
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print_config_status(config)
    else:
        print(f"❌ {message}")
        if errors:
            print("\n详细信息:")
            for error in errors:
                print(f"  {error.severity}: {error.field} - {error.message}")
        sys.exit(1)
