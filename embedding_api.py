#!/usr/bin/env python3
"""
阿里云百炼 Embedding API 封装

模型：text-embedding-v4
维度：1024

使用 urllib 直接调用 API，无需安装 dashscope 库
"""

import os
import json
import math
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# numpy 可选依赖
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


class EmbeddingAPI:
    """阿里云 DashScope Embedding API 封装（urllib 版本）

    支持文本向量化和余弦相似度计算，用于语义搜索和相似推荐。
    """

    def __init__(
        self,
        config_file: Optional[Path] = None,
        api_key: Optional[str] = None,
        model: str = "text-embedding-v4",
        dimension: int = 1024
    ) -> None:
        """
        初始化 Embedding API

        Args:
            config_file: 配置文件路径（可选），默认从技能目录加载 config.json
            api_key: 阿里云 API Key（可选），优先从配置加载，其次环境变量
            model: 模型名称，默认 text-embedding-v4
            dimension: 向量维度，默认 1024

        Raises:
            ValueError: 当 API Key 未配置时抛出
        """
        # 不再依赖 dashscope 库，直接使用 urllib
        
        # 加载 API Key
        if api_key is None:
            api_key = self._load_api_key(config_file)
        
        if not api_key:
            raise ValueError("API Key 未配置！设置 DASHSCOPE_API_KEY 环境变量或在 config.json 中配置")
        
        self.api_key = api_key
        self.model = model
        self.dimension = dimension
        # 不再使用 dashscope.api_key
        
        # 统计
        self.call_count = 0
        self.total_tokens = 0
        self.last_call = None
    
    def _load_api_key(self, config_file: Optional[Path] = None) -> str:
        """从配置或环境变量加载 API Key

        加载优先级：
        1. 环境变量 DASHSCOPE_API_KEY
        2. 配置文件 config.json 中的 api.dashscope_api_key
        3. 空字符串

        Args:
            config_file: 配置文件路径（可选）

        Returns:
            API Key 字符串，未找到时返回空字符串
        """
        # 1. 环境变量
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if api_key:
            return api_key
        
        # 2. 配置文件（统一配置）
        if config_file is None:
            skill_dir = Path(__file__).parent
            config_file = skill_dir / "config" / "config.json"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get("api", {}).get("dashscope_api_key")
                if api_key:
                    return api_key
        
        return ""
    
    def create_embedding(self, text: str, text_type: str = 'document', max_retries: int = 3) -> List[float]:
        """
        创建文本向量（使用 urllib 直接调用 API，带重试机制）

        Args:
            text: 输入文本
            text_type: 文本类型，'document' 为文档，'query' 为搜索查询
            max_retries: 最大重试次数，默认 3 次

        Returns:
            向量列表，长度为 dimension（默认 1024）

        Raises:
            Exception: 当 API 调用失败（重试后）时抛出

        Note:
            使用指数退避策略：2s, 4s, 8s
        """
        url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 添加指令前缀（提高搜索效果）
        if text_type == 'query':
            input_text = f"为这个搜索查询生成向量：{text[:2000]}"
        else:
            input_text = f"为这个文档生成向量：{text[:2000]}"
        
        payload = {
            "model": self.model,
            "input": {"texts": [input_text]}
        }
        
        # 重试机制（指数退避）
        last_error = None
        for attempt in range(max_retries):
            try:
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read().decode('utf-8'))
                    embedding = result["output"]["embeddings"][0]["embedding"]
                    self.call_count += 1
                    self.last_call = datetime.now()
                    return embedding
            except urllib.error.URLError as e:
                last_error = f"网络错误：{e}"
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避：2s, 4s, 8s
            except json.JSONDecodeError as e:
                last_error = f"响应解析失败：{e}"
                break  # 解析错误重试无用
            except KeyError as e:
                last_error = f"响应格式异常：缺少 {e}"
                break
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
        
        raise Exception(f"Embedding API 调用失败（已重试{max_retries}次）: {last_error}")
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度（支持 numpy 和纯 Python 实现）

        Args:
            vec1: 向量 1
            vec2: 向量 2

        Returns:
            相似度值，范围 [-1, 1]，值越大表示越相似

        Note:
            当 numpy 可用时使用 numpy 实现（更快），否则降级为纯 Python 实现
        """
        if HAS_NUMPY and np is not None:
            # numpy 实现（更快）
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(dot_product / (norm1 * norm2))
        else:
            # 纯 Python 实现（降级方案）
            if not vec1 or not vec2 or len(vec1) != len(vec2):
                return 0.0
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = math.sqrt(sum(a * a for a in vec1))
            norm2 = math.sqrt(sum(b * b for b in vec2))
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot_product / (norm1 * norm2)
    
    def get_stats(self) -> Dict[str, Optional[str]]:
        """获取使用统计

        Returns:
            包含统计信息的字典：
            - call_count: API 调用次数
            - total_tokens: 消耗的 token 总数
            - last_call: 最后一次调用时间
            - model: 使用的模型名称
            - dimension: 向量维度
        """
        return {
            "call_count": self.call_count,
            "total_tokens": self.total_tokens,
            "last_call": str(self.last_call) if self.last_call else None,
            "model": self.model,
            "dimension": self.dimension
        }


# 测试
if __name__ == "__main__":
    print("🚀 测试 Embedding API...")
    
    try:
        api = EmbeddingAPI()
        print(f"✅ API 初始化成功")
        print(f"   模型：{api.model}")
        print(f"   维度：{api.dimension}")
        
        # 测试向量生成
        text = "这是一个测试文本"
        embedding = api.create_embedding(text)
        print(f"✅ 向量生成成功")
        print(f"   输入：{text}")
        print(f"   维度：{len(embedding)}")
        print(f"   前 5 个值：{embedding[:5]}")
        
        # 测试相似度
        text2 = "这是另一个测试文本"
        embedding2 = api.create_embedding(text2)
        similarity = api.cosine_similarity(embedding, embedding2)
        print(f"✅ 相似度计算成功")
        print(f"   文本 1: {text}")
        print(f"   文本 2: {text2}")
        print(f"   相似度：{similarity:.4f}")
        
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
