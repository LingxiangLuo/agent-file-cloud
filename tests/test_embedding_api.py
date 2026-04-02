#!/usr/bin/env python3
"""
Embedding API 单元测试 - embedding_api.py
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from embedding_api import EmbeddingAPI


class TestEmbeddingAPIInit:
    """测试 EmbeddingAPI 初始化"""

    def test_init_with_api_key(self):
        """测试使用 API Key 初始化"""
        api = EmbeddingAPI(api_key="test_key")
        assert api.api_key == "test_key"
        assert api.model == "text-embedding-v4"
        assert api.dimension == 1024

    def test_init_custom_model(self):
        """测试自定义模型"""
        api = EmbeddingAPI(
            api_key="test_key",
            model="custom-model",
            dimension=512
        )
        assert api.model == "custom-model"
        assert api.dimension == 512

    def test_init_missing_api_key(self):
        """测试缺少 API Key 时抛出异常"""
        # 确保环境变量未设置
        original = os.environ.get("DASHSCOPE_API_KEY")
        if "DASHSCOPE_API_KEY" in os.environ:
            del os.environ["DASHSCOPE_API_KEY"]

        try:
            with pytest.raises(ValueError, match="API Key"):
                EmbeddingAPI()
        finally:
            if original:
                os.environ["DASHSCOPE_API_KEY"] = original

    def test_load_api_key_from_env(self):
        """测试从环境变量加载 API Key"""
        original = os.environ.get("DASHSCOPE_API_KEY")
        os.environ["DASHSCOPE_API_KEY"] = "env_test_key"

        try:
            api = EmbeddingAPI()
            assert api.api_key == "env_test_key"
        finally:
            if original:
                os.environ["DASHSCOPE_API_KEY"] = original
            elif "DASHSCOPE_API_KEY" in os.environ:
                del os.environ["DASHSCOPE_API_KEY"]

    def test_load_api_key_from_config(self, tmp_path):
        """测试从配置文件加载 API Key"""
        config_file = tmp_path / "config.json"
        config = {
            "api": {
                "dashscope_api_key": "config_test_key"
            }
        }
        with open(config_file, 'w') as f:
            json.dump(config, f)

        api = EmbeddingAPI(config_file=config_file)
        assert api.api_key == "config_test_key"


class TestCosineSimilarity:
    """测试余弦相似度计算"""

    def test_cosine_similarity_identical(self):
        """测试相同向量的相似度"""
        api = EmbeddingAPI(api_key="test")
        vec = [1.0, 2.0, 3.0]
        similarity = api.cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 0.0001

    def test_cosine_similarity_orthogonal(self):
        """测试正交向量的相似度"""
        api = EmbeddingAPI(api_key="test")
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = api.cosine_similarity(vec1, vec2)
        assert abs(similarity) < 0.0001

    def test_cosine_similarity_opposite(self):
        """测试相反向量的相似度"""
        api = EmbeddingAPI(api_key="test")
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        similarity = api.cosine_similarity(vec1, vec2)
        assert abs(similarity + 1.0) < 0.0001

    def test_cosine_similarity_empty(self):
        """测试空向量"""
        api = EmbeddingAPI(api_key="test")
        similarity = api.cosine_similarity([], [])
        assert similarity == 0.0

    def test_cosine_similarity_different_length(self):
        """测试不同长度的向量"""
        api = EmbeddingAPI(api_key="test")
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]
        similarity = api.cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    def test_cosine_similarity_zero_vector(self):
        """测试零向量"""
        api = EmbeddingAPI(api_key="test")
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        similarity = api.cosine_similarity(vec1, vec2)
        assert similarity == 0.0


class TestGetStats:
    """测试统计信息"""

    def test_get_stats_initial(self):
        """测试初始统计"""
        api = EmbeddingAPI(api_key="test")
        stats = api.get_stats()

        assert stats["call_count"] == 0
        assert stats["total_tokens"] == 0
        assert stats["last_call"] is None
        assert stats["model"] == "text-embedding-v4"
        assert stats["dimension"] == 1024

    def test_get_stats_after_call(self):
        """测试调用后统计"""
        api = EmbeddingAPI(api_key="test")
        api.call_count = 5
        api.total_tokens = 1000

        stats = api.get_stats()
        assert stats["call_count"] == 5
        assert stats["total_tokens"] == 1000


class TestCreateEmbedding:
    """测试向量生成（mock 测试）"""

    @patch('urllib.request.urlopen')
    def test_create_embedding_success(self, mock_urlopen):
        """测试成功生成向量"""
        # 设置 mock 响应
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "output": {
                "embeddings": [{
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
                }]
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        api = EmbeddingAPI(api_key="test_key")
        embedding = api.create_embedding("test text")

        assert len(embedding) == 5
        assert embedding[0] == 0.1
        assert api.call_count == 1

    @patch('urllib.request.urlopen')
    def test_create_embedding_with_type(self, mock_urlopen):
        """测试带文本类型的向量生成"""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "output": {
                "embeddings": [{
                    "embedding": [0.1, 0.2, 0.3]
                }]
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        api = EmbeddingAPI(api_key="test_key")
        api.create_embedding("test query", text_type='query')

        # 验证调用了 API
        assert api.call_count == 1

    @patch('urllib.request.urlopen')
    def test_create_embedding_retry(self, mock_urlopen):
        """测试重试机制"""
        import urllib.error

        # 前两次失败，第三次成功
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "output": {
                "embeddings": [{
                    "embedding": [0.1, 0.2, 0.3]
                }]
            }
        }).encode('utf-8')

        mock_urlopen.side_effect = [
            urllib.error.URLError("Network error"),
            urllib.error.URLError("Network error"),
            mock_response
        ]

        api = EmbeddingAPI(api_key="test_key")
        embedding = api.create_embedding("test text", max_retries=3)

        assert len(embedding) == 3
        assert api.call_count == 1

    @patch('urllib.request.urlopen')
    def test_create_embedding_max_retries_exceeded(self, mock_urlopen):
        """测试超过最大重试次数"""
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("Network error")

        api = EmbeddingAPI(api_key="test_key")

        with pytest.raises(Exception):
            api.create_embedding("test text", max_retries=2)

    @patch('urllib.request.urlopen')
    def test_create_embedding_json_error(self, mock_urlopen):
        """测试 JSON 解析错误"""
        mock_response = MagicMock()
        mock_response.read.return_value = b"invalid json"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        api = EmbeddingAPI(api_key="test_key")

        with pytest.raises(Exception):
            api.create_embedding("test text", max_retries=1)
