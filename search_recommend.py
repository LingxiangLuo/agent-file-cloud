#!/usr/bin/env python3
"""
智能检索与推荐系统 v4.0

基于：
- 🔗 向量相似度（Embedding）
- 🕸️ 知识图谱（Graph）
- 📊 混合排序（Hybrid Ranking）

功能：
- 语义检索
- 图谱检索
- 混合推荐
- 智能排序
"""

import json
import math
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, OrderedDict
from functools import lru_cache

# 技能目录
SKILL_DIR = Path(__file__).parent
from data_manager import DataManager


class LRUCache:
    """简单的 LRU 缓存实现"""

    def __init__(self, max_size: int = 100):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[any]:
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def put(self, key: str, value: any):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def clear(self):
        self.cache.clear()

    def stats(self) -> Dict:
        total = self.hits + self.misses
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0
        }


class SearchAndRecommend:
    """智能检索与推荐系统 v4.0"""

    def __init__(self, cache_size: int = 100):
        """初始化检索推荐系统"""
        self.dm = DataManager()
        # 缓存机制
        self.search_cache = LRUCache(max_size=cache_size)  # 搜索结果缓存
        self.recommend_cache = LRUCache(max_size=cache_size)  # 推荐结果缓存
        self._cache_ttl = {}  # 缓存过期时间
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={json.dumps(v, sort_keys=True)}")
        return "|".join(key_parts)

    def _is_cache_expired(self, key: str, ttl_seconds: int = 300) -> bool:
        """检查缓存是否过期"""
        if key not in self._cache_ttl:
            return True
        return time.time() > self._cache_ttl[key]

    def _set_cache_with_ttl(self, key: str, value: any, ttl_seconds: int = 300):
        """设置带过期时间的缓存"""
        self.search_cache.put(key, value)
        self._cache_ttl[key] = time.time() + ttl_seconds

    def clear_cache(self):
        """清空所有缓存"""
        self.search_cache.clear()
        self.recommend_cache.clear()
        self._cache_ttl.clear()

    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        return {
            "search_cache": self.search_cache.stats(),
            "recommend_cache": self.recommend_cache.stats()
        }

    # ========== 向量相似度计算 ==========
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def semantic_search(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int = 10,
        min_similarity: float = 0.5,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        语义检索（基于向量相似度）

        Args:
            query: 搜索查询
            query_embedding: 查询向量
            top_k: 返回数量
            min_similarity: 最小相似度阈值
            use_cache: 是否使用缓存

        Returns:
            搜索结果列表
        """
        # 生成缓存键（使用向量前 10 维的哈希作为键的一部分）
        emb_hash = hash(tuple(round(x, 4) for x in query_embedding[:10]))
        cache_key = self._get_cache_key(
            "semantic",
            query=query,
            emb_hash=emb_hash,
            top_k=top_k,
            min_similarity=min_similarity
        )

        # 尝试从缓存获取
        if use_cache:
            cached_result = self.search_cache.get(cache_key)
            if cached_result and not self._is_cache_expired(cache_key):
                return cached_result

        results = []

        # 获取所有文件的向量
        for file_id, emb_data in self.dm.vectors["embeddings"].items():
            file_embedding = emb_data["embedding"]

            # 计算相似度
            similarity = self.cosine_similarity(query_embedding, file_embedding)

            if similarity >= min_similarity:
                # 获取文件元数据
                file_metadata = self.dm.get_file_metadata(file_id)
                if file_metadata:
                    results.append({
                        "file_id": file_id,
                        "filename": file_metadata.get("filename", ""),
                        "description": file_metadata.get("description", ""),
                        "category": file_metadata.get("category", ""),
                        "tags": file_metadata.get("tags", []),
                        "score": similarity,
                        "search_type": "semantic"
                    })

        # 按相似度排序
        results.sort(key=lambda x: x["score"], reverse=True)
        limited_results = results[:top_k]

        # 缓存结果（5 分钟 TTL）
        if use_cache:
            self._set_cache_with_ttl(cache_key, limited_results, ttl_seconds=300)

        return limited_results
    
    # ========== 图谱检索 ==========
    
    def graph_search(
        self,
        file_id: str,
        max_depth: int = 2,
        relation_types: List[str] = None
    ) -> List[Dict]:
        """
        图谱检索（基于知识图谱）
        
        Args:
            file_id: 源文件 ID
            max_depth: 最大深度
            relation_types: 关系类型过滤
        
        Returns:
            相关文件列表
        """
        return self.dm.get_related_files(file_id, max_depth=max_depth)
    
    def search_by_category(self, category: str, limit: int = 20) -> List[Dict]:
        """按分类检索"""
        files = self.dm.list_files(category=category, limit=limit)
        return [
            {
                "file_id": f["id"],
                "filename": f["filename"],
                "category": f["category"],
                "tags": f["tags"],
                "description": f.get("description", ""),
                "search_type": "category"
            }
            for f in files
        ]
    
    def search_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict]:
        """
        按标签检索
        
        Args:
            tags: 标签列表
            match_all: 是否匹配所有标签
        """
        files = self.dm.list_files(tags=tags, limit=100)
        
        results = []
        for f in files:
            file_tags = set(f.get("tags", []))
            query_tags = set(tags)
            
            if match_all:
                if query_tags.issubset(file_tags):
                    results.append({
                        "file_id": f["id"],
                        "filename": f["filename"],
                        "category": f["category"],
                        "tags": f["tags"],
                        "matched_tags": list(query_tags & file_tags),
                        "search_type": "tags_all"
                    })
            else:
                if query_tags & file_tags:  # 有交集
                    results.append({
                        "file_id": f["id"],
                        "filename": f["filename"],
                        "category": f["category"],
                        "tags": f["tags"],
                        "matched_tags": list(query_tags & file_tags),
                        "search_type": "tags_any"
                    })
        
        # 按匹配标签数排序
        results.sort(key=lambda x: len(x["matched_tags"]), reverse=True)
        
        return results
    
    # ========== 混合推荐 ==========
    
    def hybrid_recommend(
        self,
        file_id: str,
        top_k: int = 10,
        use_embedding: bool = True,
        use_graph: bool = True,
        embedding_weight: float = 0.6,
        graph_weight: float = 0.4,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        混合推荐（向量 + 图谱）

        Args:
            file_id: 源文件 ID
            top_k: 推荐数量
            use_embedding: 是否使用向量相似度
            use_graph: 是否使用图谱
            embedding_weight: 向量权重
            graph_weight: 图谱权重
            use_cache: 是否使用缓存

        Returns:
            推荐结果列表
        """
        # 生成缓存键
        cache_key = self._get_cache_key(
            "hybrid",
            file_id=file_id,
            top_k=top_k,
            use_embedding=use_embedding,
            use_graph=use_graph,
            embedding_weight=embedding_weight,
            graph_weight=graph_weight
        )

        # 尝试从缓存获取
        if use_cache:
            cached_result = self.recommend_cache.get(cache_key)
            if cached_result and not self._is_cache_expired(cache_key, ttl_seconds=600):
                return cached_result

        scores: Dict[str, Dict] = defaultdict(lambda: {
            "semantic_score": 0.0,
            "graph_score": 0.0,
            "combined_score": 0.0
        })

        # 1. 向量相似度推荐
        if use_embedding:
            source_embedding = self.dm.get_embedding(file_id)
            if source_embedding:
                for fid, emb_data in self.dm.vectors["embeddings"].items():
                    if fid == file_id:
                        continue

                    similarity = self.cosine_similarity(
                        source_embedding,
                        emb_data["embedding"]
                    )

                    if similarity > 0.7:  # 高相似度阈值
                        scores[fid]["semantic_score"] = similarity
                        scores[fid]["file_id"] = fid

        # 2. 图谱推荐
        if use_graph:
            related = self.dm.get_related_files(file_id, max_depth=2)
            for r in related:
                fid = r["file_id"]
                relation = r.get("relation", "unknown")

                # 根据关系类型给分
                if relation == "direct":
                    graph_score = 1.0
                elif relation == "indirect":
                    graph_score = 0.7
                elif relation.startswith("category"):
                    graph_score = 0.6
                elif relation.startswith("tags"):
                    graph_score = 0.8
                else:
                    graph_score = 0.5

                scores[fid]["graph_score"] = max(
                    scores[fid]["graph_score"],
                    graph_score
                )
                scores[fid]["file_id"] = fid

        # 3. 合并分数
        results = []
        for fid, score_data in scores.items():
            if score_data["semantic_score"] == 0 and score_data["graph_score"] == 0:
                continue

            # 加权合并
            combined = (
                score_data["semantic_score"] * embedding_weight +
                score_data["graph_score"] * graph_weight
            )

            # 获取文件元数据
            file_metadata = self.dm.get_file_metadata(fid)
            if file_metadata:
                results.append({
                    "file_id": fid,
                    "filename": file_metadata.get("filename", ""),
                    "category": file_metadata.get("category", ""),
                    "tags": file_metadata.get("tags", []),
                    "description": file_metadata.get("description", ""),
                    "semantic_score": score_data["semantic_score"],
                    "graph_score": score_data["graph_score"],
                    "combined_score": combined,
                    "recommendation_type": "hybrid"
                })

        # 按综合分数排序
        results.sort(key=lambda x: x["combined_score"], reverse=True)
        limited_results = results[:top_k]

        # 缓存结果（10 分钟 TTL）
        if use_cache:
            self._set_cache_with_ttl(cache_key, limited_results, ttl_seconds=600)

        return limited_results
    
    def recommend_by_category(
        self,
        file_id: str,
        top_k: int = 5
    ) -> List[Dict]:
        """基于分类的推荐"""
        file_metadata = self.dm.get_file_metadata(file_id)
        if not file_metadata:
            return []
        
        category = file_metadata.get("category")
        files = self.dm.list_files(category=category, limit=top_k + 1)
        
        # 排除源文件
        results = [
            {
                "file_id": f["id"],
                "filename": f["filename"],
                "category": f["category"],
                "tags": f["tags"],
                "description": f.get("description", ""),
                "recommendation_type": "category"
            }
            for f in files if f["id"] != file_id
        ]
        
        return results[:top_k]
    
    def recommend_by_tags(
        self,
        file_id: str,
        top_k: int = 5
    ) -> List[Dict]:
        """基于标签的推荐"""
        file_metadata = self.dm.get_file_metadata(file_id)
        if not file_metadata:
            return []
        
        tags = file_metadata.get("tags", [])
        if not tags:
            return []
        
        # 查找有相同标签的文件
        files = self.dm.list_files(tags=tags, limit=top_k * 2)
        
        results = []
        for f in files:
            if f["id"] == file_id:
                continue
            
            common_tags = set(tags) & set(f.get("tags", []))
            if common_tags:
                results.append({
                    "file_id": f["id"],
                    "filename": f["filename"],
                    "category": f["category"],
                    "tags": f["tags"],
                    "common_tags": list(common_tags),
                    "recommendation_type": "tags"
                })
        
        # 按共同标签数排序
        results.sort(key=lambda x: len(x["common_tags"]), reverse=True)
        
        return results[:top_k]
    
    # ========== 智能检索 ==========
    
    def smart_search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 10,
        filters: Dict = None
    ) -> List[Dict]:
        """
        智能检索（多策略融合）
        
        Args:
            query: 搜索查询
            query_embedding: 查询向量（可选）
            top_k: 返回数量
            filters: 过滤器 {category, tags, date_range}
        
        Returns:
            搜索结果
        """
        results = []
        seen_ids = set()
        
        # 1. 语义检索（如果有向量）
        if query_embedding:
            semantic_results = self.semantic_search(
                query,
                query_embedding,
                top_k=top_k,
                min_similarity=0.5
            )
            for r in semantic_results:
                results.append(r)
                seen_ids.add(r["file_id"])
        
        # 2. 关键词检索（元数据）
        query_lower = query.lower()
        for file_id, file_data in self.dm.metadata["files"].items():
            if file_id in seen_ids:
                continue
            
            # 搜索文件名、描述、标签
            match_score = 0
            
            if query_lower in file_data.get("filename", "").lower():
                match_score += 3
            
            if query_lower in file_data.get("description", "").lower():
                match_score += 2
            
            if any(query_lower in tag.lower() for tag in file_data.get("tags", [])):
                match_score += 1
            
            if match_score > 0:
                results.append({
                    "file_id": file_id,
                    "filename": file_data.get("filename", ""),
                    "category": file_data.get("category", ""),
                    "tags": file_data.get("tags", []),
                    "description": file_data.get("description", ""),
                    "score": match_score / 3.0,
                    "search_type": "keyword"
                })
                seen_ids.add(file_id)
        
        # 3. 应用过滤器
        if filters:
            filtered_results = []
            for r in results:
                match = True
                
                if "category" in filters:
                    if r.get("category") != filters["category"]:
                        match = False
                
                if "tags" in filters:
                    file_tags = set(r.get("tags", []))
                    if not set(filters["tags"]) & file_tags:
                        match = False
                
                if match:
                    filtered_results.append(r)
            
            results = filtered_results
        
        # 4. 排序
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return results[:top_k]
    
    # ========== 统计与报告 ==========
    
    def get_search_stats(self) -> Dict:
        """获取检索统计"""
        vectors_count = len(self.dm.vectors["embeddings"])
        files_count = len(self.dm.metadata["files"])

        # 计算向量覆盖率
        coverage = vectors_count / files_count if files_count > 0 else 0

        # 缓存统计
        cache_stats = self.get_cache_stats()

        return {
            "total_files": files_count,
            "files_with_embedding": vectors_count,
            "embedding_coverage": coverage,
            "graph_nodes": len(self.dm.graph["nodes"]),
            "graph_edges": len(self.dm.graph["edges"]),
            "cache": cache_stats,
            "optimization_suggestions": [
                "对于大规模数据（>1000 文件），建议使用 FAISS 进行向量索引",
                "安装 FAISS: pip install faiss-cpu",
                "当前已启用 LRU 缓存减少重复计算"
            ]
        }
    
    def print_recommendations(self, file_id: str, top_k: int = 5):
        """打印推荐结果"""
        print(f"\n📌 为文件推荐相似文件 (ID: {file_id})")
        print("=" * 50)
        
        # 混合推荐
        recommendations = self.hybrid_recommend(file_id, top_k=top_k)
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. 📄 {rec['filename']}")
                print(f"   分类：{rec['category']}")
                print(f"   标签：{', '.join(rec['tags'])}")
                print(f"   综合得分：{rec['combined_score']:.2f}")
                print(f"   - 向量相似度：{rec['semantic_score']:.2f}")
                print(f"   - 图谱关联度：{rec['graph_score']:.2f}")
        else:
            print("❌ 没有找到推荐文件")
            print("\n💡 建议:")
            print("   1. 添加更多文件到系统")
            print("   2. 为文件生成 Embedding 向量")
            print("   3. 完善文件标签和分类")


# CLI
if __name__ == "__main__":
    import sys
    
    sar = SearchAndRecommend()
    
    if len(sys.argv) < 2:
        print("智能检索与推荐系统 v4.0")
        print("\n用法:")
        print("  search_recommend.py stats              # 查看统计")
        print("  search_recommend.py recommend <id>     # 推荐相似文件")
        print("  search_recommend.py search <query>     # 智能检索")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "stats":
        stats = sar.get_search_stats()
        print("📊 检索与推荐统计")
        print("=" * 50)
        print(f"总文件数：{stats['total_files']}")
        print(f"已向量化：{stats['files_with_embedding']}")
        print(f"向量覆盖率：{stats['embedding_coverage']:.0%}")
        print(f"图谱节点：{stats['graph_nodes']}")
        print(f"图谱边：{stats['graph_edges']}")
        print("\n📦 缓存统计:")
        cache = stats['cache']
        print(f"   搜索缓存：{cache['search_cache']['size']} 条 (命中率：{cache['search_cache']['hit_rate']:.1%})")
        print(f"   推荐缓存：{cache['recommend_cache']['size']} 条 (命中率：{cache['recommend_cache']['hit_rate']:.1%})")
        print("\n💡 优化建议:")
        for sug in stats.get('optimization_suggestions', []):
            print(f"   - {sug}")
    
    elif command == "recommend":
        if len(sys.argv) < 3:
            print("❌ 错误：请指定文件 ID")
            sys.exit(1)
        
        file_id = sys.argv[2]
        sar.print_recommendations(file_id)
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("❌ 错误：请指定搜索查询")
            sys.exit(1)
        
        query = sys.argv[2]
        print(f"🔍 搜索：{query}")
        print("⚠️  需要 Embedding 向量才能进行语义搜索")
        print("💡 请先为文件生成向量")
    
    else:
        print(f"❌ 未知命令：{command}")
