#!/usr/bin/env python3
"""
核心数据管理器 v4.0

整合管理：
- 📄 文件元数据管理
- 📚 版本管理
- 📜 历史记录管理
- 🔗 向量数据管理
- 🕸️ 知识图谱管理
"""

import json
import hashlib
import time
import fcntl
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

# networkx 可选依赖
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None  # type: ignore[assignment]


# 技能目录
SKILL_DIR = Path(__file__).parent
CONFIG_FILE = SKILL_DIR / "config" / "config.json"

# 数据文件
METADATA_DB = SKILL_DIR / "config" / "metadata.json"
VERSIONS_DB = SKILL_DIR / "config" / "versions.json"
HISTORY_DB = SKILL_DIR / "config" / "history.json"
VECTORS_DB = SKILL_DIR / "config" / "vectors.json"
GRAPH_DB = SKILL_DIR / "config" / "graph.json"


class DataManager:
    """核心数据管理器 v4.0

    负责管理文件的元数据、版本、历史记录、向量和知识图谱。
    所有数据持久化到 JSON 文件，支持文件锁保证并发安全。
    """

    def __init__(self) -> None:
        """初始化数据管理器，加载所有数据文件到内存"""
        self.config = self._load_config()
        self.metadata = self._load_metadata()
        self.versions = self._load_versions()
        self.history = self._load_history()
        self.vectors = self._load_vectors()
        self.graph = self._load_graph()
    
    def _load_config(self) -> Dict:
        """加载配置文件

        Returns:
            配置字典，文件不存在时返回空字典
        """
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_metadata(self) -> Dict:
        """加载元数据文件

        Returns:
            元数据字典，包含 files 和 next_id 字段
        """
        if METADATA_DB.exists():
            with open(METADATA_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"files": {}, "next_id": 1}
    
    def _save_metadata(self):
        """保存元数据（带文件锁）"""
        METADATA_DB.parent.mkdir(parents=True, exist_ok=True)
        with open(METADATA_DB, 'w', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 获取排他锁
            try:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 释放锁
    
    def _load_versions(self) -> Dict:
        """加载版本数据文件

        Returns:
            版本数据字典，包含 versions 列表
        """
        if VERSIONS_DB.exists():
            with open(VERSIONS_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"versions": []}
    
    def _save_versions(self):
        """保存版本数据（带文件锁）"""
        with open(VERSIONS_DB, 'w', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(self.versions, f, indent=2, ensure_ascii=False)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def _load_history(self) -> Dict:
        """加载操作历史文件

        Returns:
            操作历史字典，包含 operations 列表
        """
        if HISTORY_DB.exists():
            with open(HISTORY_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"operations": []}
    
    def _save_history(self):
        """保存操作历史（带文件锁）"""
        with open(HISTORY_DB, 'w', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def _load_vectors(self) -> Dict:
        """加载向量数据文件

        Returns:
            向量数据字典，包含 embeddings 字典
        """
        if VECTORS_DB.exists():
            with open(VECTORS_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"embeddings": {}}
    
    def _save_vectors(self):
        """保存向量数据（带文件锁）"""
        with open(VECTORS_DB, 'w', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(self.vectors, f, indent=2, ensure_ascii=False)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def _load_graph(self) -> Dict:
        """加载知识图谱文件

        Returns:
            图谱数据字典，包含 nodes 和 edges 列表
        """
        if GRAPH_DB.exists():
            with open(GRAPH_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"nodes": [], "edges": []}
    
    def _save_graph(self):
        """保存图谱数据（带文件锁）"""
        with open(GRAPH_DB, 'w', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(self.graph, f, indent=2, ensure_ascii=False)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    # ========== 文件元数据管理 ==========

    def generate_file_id(self, filepath: str) -> str:
        """生成唯一文件 ID

        Args:
            filepath: 文件路径（用于生成 ID，但不直接包含在 ID 中）

        Returns:
            唯一文件 ID，格式为 file_<uuid4 hex>
        """
        return f"file_{uuid.uuid4().hex}"

    def add_file_metadata(
        self,
        filepath: str,
        filename: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        category: str = "uncategorized",
        project: str = "",
        **kwargs
    ) -> str:
        """
        添加文件元数据到数据库

        Args:
            filepath: 文件路径
            filename: 文件名（可选，默认从路径提取）
            description: 文件描述
            tags: 标签列表
            category: 分类
            project: 所属项目
            **kwargs: 其他元数据字段

        Returns:
            生成的文件 ID

        Raises:
            FileNotFoundError: 当文件不存在时抛出
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"文件不存在：{filepath}")
        
        file_id = self.generate_file_id(str(filepath))
        with open(filepath, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        metadata = {
            "id": file_id,
            "path": str(filepath),
            "filename": filename or filepath.name,
            "size": filepath.stat().st_size,
            "file_hash": file_hash,
            "category": category,
            "tags": tags or [],
            "description": description,
            "project": project,
            "created_at": datetime.now().isoformat(),
            "created_by": "OpenClaw-Agent",
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "qiniu_id": None,
            "qiniu_url": None,
            "qiniu_expiry": None,
            "access_count": 0,
            "last_accessed": None,
            **kwargs
        }
        
        self.metadata["files"][file_id] = metadata
        self.metadata["next_id"] += 1
        self._save_metadata()
        
        # 记录操作历史
        self._log_operation("add_file", file_id, {"path": str(filepath)})
        
        # 添加到图谱
        self._add_file_to_graph(file_id, metadata)
        
        return file_id
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict]:
        """获取文件元数据

        Args:
            file_id: 文件 ID

        Returns:
            文件元数据字典，不存在时返回 None
        """
        file_data = self.metadata["files"].get(file_id)
        if file_data:
            # 更新访问记录
            file_data["access_count"] += 1
            file_data["last_accessed"] = datetime.now().isoformat()
            self._save_metadata()
        return file_data
    
    def update_file_metadata(self, file_id: str, **updates) -> bool:
        """更新文件元数据

        Args:
            file_id: 文件 ID
            **updates: 要更新的字段

        Returns:
            是否更新成功（文件不存在时返回 False）
        """
        if file_id not in self.metadata["files"]:
            return False
        
        file_data = self.metadata["files"][file_id]
        file_data.update(updates)
        file_data["updated_at"] = datetime.now().isoformat()
        
        # 版本号 +1
        file_data["version"] += 1
        
        self._save_metadata()
        self._log_operation("update_metadata", file_id, updates)
        
        return True
    
    def delete_file_metadata(self, file_id: str) -> bool:
        """删除文件元数据及相关向量和图谱节点

        Args:
            file_id: 文件 ID

        Returns:
            是否删除成功（文件不存在时返回 False）
        """
        if file_id not in self.metadata["files"]:
            return False
        
        del self.metadata["files"][file_id]
        self._save_metadata()
        
        # 删除相关向量
        if file_id in self.vectors["embeddings"]:
            del self.vectors["embeddings"][file_id]
            self._save_vectors()
        
        # 从图谱中移除
        self._remove_from_graph(file_id)
        
        self._log_operation("delete_file", file_id, {})
        
        return True
    
    def list_files(self, limit: int = 20, category: Optional[str] = None,
                   tags: Optional[List[str]] = None) -> List[Dict]:
        """列出文件（支持筛选）

        Args:
            limit: 返回数量限制
            category: 分类筛选（可选）
            tags: 标签筛选（可选）

        Returns:
            文件列表，按创建时间倒序
        """
        files = list(self.metadata["files"].values())
        
        # 按分类筛选
        if category:
            files = [f for f in files if f.get("category") == category]
        
        # 按标签筛选
        if tags:
            files = [f for f in files if any(t in f.get("tags", []) for t in tags)]
        
        # 按创建时间排序（最新的在前）
        files.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return files[:limit]
    
    # ========== 版本管理 ==========

    def create_version(
        self,
        file_id: str,
        version_path: str,
        version_name: Optional[str] = None,
        description: str = "",
        change_type: str = "update"
    ) -> str:
        """
        创建新版本

        Args:
            file_id: 文件 ID
            version_path: 版本文件路径
            version_name: 版本名称（如 v1.0, v2.0），默认自动生成
            description: 版本描述
            change_type: 变更类型 (create/update/rename/move)

        Returns:
            版本 ID

        Raises:
            FileNotFoundError: 当版本文件不存在时抛出
            ValueError: 当文件 ID 不存在时抛出
        """
        version_path = Path(version_path)
        if not version_path.exists():
            raise FileNotFoundError(f"版本文件不存在：{version_path}")
        
        version_id = f"ver_{int(time.time() * 1000)}"
        
        # 获取当前文件信息
        file_data = self.get_file_metadata(file_id)
        if not file_data:
            raise ValueError(f"文件不存在：{file_id}")
        
        version = {
            "version_id": version_id,
            "file_id": file_id,
            "version_number": file_data["version"],
            "version_name": version_name or f"v{file_data['version']}.0",
            "path": str(version_path),
            "size": version_path.stat().st_size,
            "file_hash": hashlib.md5(open(version_path, 'rb').read()).hexdigest(),
            "description": description,
            "change_type": change_type,
            "created_at": datetime.now().isoformat(),
            "created_by": "OpenClaw-Agent",
            "parent_version": None  # 父版本 ID
        }
        
        # 查找父版本
        existing_versions = [v for v in self.versions["versions"] 
                           if v["file_id"] == file_id]
        if existing_versions:
            existing_versions.sort(key=lambda x: x["created_at"], reverse=True)
            version["parent_version"] = existing_versions[0]["version_id"]
        
        self.versions["versions"].append(version)
        self._save_versions()
        self._log_operation("create_version", file_id, {
            "version_id": version_id,
            "version_name": version["version_name"]
        })
        
        return version_id
    
    def get_version_history(self, file_id: str) -> List[Dict]:
        """获取文件版本历史

        Args:
            file_id: 文件 ID

        Returns:
            版本列表，按版本号倒序排列
        """
        versions = [v for v in self.versions["versions"] 
                   if v["file_id"] == file_id]
        versions.sort(key=lambda x: x["version_number"], reverse=True)
        return versions
    
    def restore_version(self, version_id: str) -> bool:
        """恢复指定版本到文件

        Args:
            version_id: 版本 ID

        Returns:
            是否恢复成功（版本不存在时返回 False）

        Raises:
            FileNotFoundError: 当版本文件不存在时抛出
        """
        version = None
        for v in self.versions["versions"]:
            if v["version_id"] == version_id:
                version = v
                break
        
        if not version:
            return False
        
        file_id = version["file_id"]
        version_path = Path(version["path"])
        
        if not version_path.exists():
            raise FileNotFoundError(f"版本文件不存在：{version_path}")
        
        # 恢复文件内容
        file_data = self.get_file_metadata(file_id)
        if file_data:
            # 复制版本文件到原位置
            import shutil
            shutil.copy2(version_path, file_data["path"])
            
            # 更新元数据
            self.update_file_metadata(file_id, 
                                     description=f"恢复到版本 {version['version_name']}")
        
        self._log_operation("restore_version", file_id, {
            "version_id": version_id
        })
        
        return True
    
    # ========== 历史记录管理 ==========
    
    def _log_operation(self, operation: str, file_id: str, details: Dict) -> None:
        """记录操作历史

        Args:
            operation: 操作类型（如 add_file, update_metadata 等）
            file_id: 文件 ID
            details: 操作详情字典
        """
        record = {
            "operation_id": f"op_{int(time.time() * 1000)}",
            "operation": operation,
            "file_id": file_id,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "by": "OpenClaw-Agent"
        }
        self.history["operations"].append(record)
        
        # 保留最近 1000 条记录
        if len(self.history["operations"]) > 1000:
            self.history["operations"] = self.history["operations"][-1000:]
        
        self._save_history()
    
    def get_operation_history(self, file_id: Optional[str] = None,
                             limit: int = 50) -> List[Dict]:
        """获取操作历史

        Args:
            file_id: 文件 ID（可选，只获取该文件的历史）
            limit: 返回数量限制

        Returns:
            操作历史记录列表，按时间倒序
        """
        operations = self.history["operations"]
        
        if file_id:
            operations = [op for op in operations if op["file_id"] == file_id]
        
        operations.sort(key=lambda x: x["timestamp"], reverse=True)
        return operations[:limit]
    
    # ========== 向量数据管理 ==========
    
    def save_embedding(self, file_id: str, embedding: List[float],
                      model: str = "text-embedding-v4") -> bool:
        """保存文件向量

        Args:
            file_id: 文件 ID
            embedding: 向量数据
            model: 模型名称

        Returns:
            是否保存成功
        """
        self.vectors["embeddings"][file_id] = {
            "embedding": embedding,
            "model": model,
            "dimension": len(embedding),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self._save_vectors()
        return True
    
    def get_embedding(self, file_id: str) -> Optional[List[float]]:
        """获取文件向量

        Args:
            file_id: 文件 ID

        Returns:
            向量数据，不存在时返回 None
        """
        emb_data = self.vectors["embeddings"].get(file_id)
        if emb_data:
            return emb_data["embedding"]
        return None
    
    def has_embedding(self, file_id: str) -> bool:
        """检查文件是否有向量

        Args:
            file_id: 文件 ID

        Returns:
            是否有向量数据
        """
        return file_id in self.vectors["embeddings"]
    
    def get_all_embeddings(self) -> Dict[str, List[float]]:
        """获取所有文件的向量

        Returns:
            文件 ID 到向量的映射字典
        """
        return {
            file_id: data["embedding"] 
            for file_id, data in self.vectors["embeddings"].items()
        }
    
    def delete_embedding(self, file_id: str) -> bool:
        """删除文件向量

        Args:
            file_id: 文件 ID

        Returns:
            是否删除成功（文件不存在时返回 False）
        """
        if file_id in self.vectors["embeddings"]:
            del self.vectors["embeddings"][file_id]
            self._save_vectors()
            return True
        return False
    
    # ========== 知识图谱管理 ==========
    
    def _add_file_to_graph(self, file_id: str, metadata: Dict) -> None:
        """添加文件到知识图谱

        Args:
            file_id: 文件 ID
            metadata: 文件元数据
        """
        node = {
            "id": file_id,
            "type": "file",
            "filename": metadata.get("filename", ""),
            "category": metadata.get("category", ""),
            "tags": metadata.get("tags", []),
            "created_at": metadata.get("created_at", "")
        }
        
        self.graph["nodes"].append(node)
        self._save_graph()
        
        # 添加分类边
        category = metadata.get("category")
        if category:
            # 确保分类节点存在
            category_node = next((n for n in self.graph["nodes"] 
                                if n["id"] == f"cat_{category}"), None)
            if not category_node:
                self.graph["nodes"].append({
                    "id": f"cat_{category}",
                    "type": "category",
                    "name": category
                })
            
            # 添加边
            self.graph["edges"].append({
                "source": file_id,
                "target": f"cat_{category}",
                "type": "belongs_to",
                "created_at": datetime.now().isoformat()
            })
        
        # 添加标签边
        for tag in metadata.get("tags", []):
            tag_id = f"tag_{tag}"
            tag_node = next((n for n in self.graph["nodes"] 
                           if n["id"] == tag_id), None)
            if not tag_node:
                self.graph["nodes"].append({
                    "id": tag_id,
                    "type": "tag",
                    "name": tag
                })
            
            self.graph["edges"].append({
                "source": file_id,
                "target": tag_id,
                "type": "tagged_with",
                "created_at": datetime.now().isoformat()
            })
        
        self._save_graph()
    
    def _remove_from_graph(self, file_id: str) -> None:
        """从知识图谱中移除文件节点及相关边

        Args:
            file_id: 文件 ID
        """
        # 移除节点
        self.graph["nodes"] = [n for n in self.graph["nodes"] 
                              if n["id"] != file_id]
        
        # 移除相关边
        self.graph["edges"] = [e for e in self.graph["edges"] 
                              if e["source"] != file_id and e["target"] != file_id]
        
        self._save_graph()
    
    def add_graph_edge(self, source_id: str, target_id: str,
                      edge_type: str = "related_to") -> None:
        """添加知识图谱边

        Args:
            source_id: 源节点 ID
            target_id: 目标节点 ID
            edge_type: 边类型
        """
        edge = {
            "source": source_id,
            "target": target_id,
            "type": edge_type,
            "created_at": datetime.now().isoformat()
        }
        self.graph["edges"].append(edge)
        self._save_graph()
        self._log_operation("add_edge", source_id, {
            "target": target_id,
            "type": edge_type
        })
    
    def get_related_files(self, file_id: str,
                         max_depth: int = 2) -> List[Dict]:
        """获取相关文件（基于图谱或相似度）

        Args:
            file_id: 文件 ID
            max_depth: 最大深度（1=直接关联，2=间接关联）

        Returns:
            相关文件列表，包含文件信息和关联类型
        """
        if not HAS_NETWORKX:
            # 简化版本（无 networkx）
            related = []
            # 查找同分类的文件
            file_data = self.get_file_metadata(file_id)
            if file_data:
                category = file_data.get("category")
                tags = file_data.get("tags", [])
                
                for fid, fdata in self.metadata["files"].items():
                    if fid == file_id:
                        continue
                    
                    # 同分类
                    if fdata.get("category") == category:
                        related.append({
                            "file_id": fid,
                            "filename": fdata.get("filename", ""),
                            "category": category,
                            "tags": fdata.get("tags", []),
                            "relation": "category"
                        })
                    
                    # 同标签
                    common_tags = set(tags) & set(fdata.get("tags", []))
                    if common_tags:
                        related.append({
                            "file_id": fid,
                            "filename": fdata.get("filename", ""),
                            "category": fdata.get("category", ""),
                            "tags": fdata.get("tags", []),
                            "relation": f"tags:{','.join(common_tags)}"
                        })
            
            return related
        
        # 完整版本（使用 networkx）
        # 使用 networkx 构建临时图
        G = nx.DiGraph()
        
        # 添加节点
        for node in self.graph["nodes"]:
            G.add_node(node["id"], **node)
        
        # 添加边
        for edge in self.graph["edges"]:
            G.add_edge(edge["source"], edge["target"], type=edge["type"])
        
        # 查找相关文件
        related = []
        try:
            # 获取邻居节点
            neighbors = list(G.neighbors(file_id))
            for neighbor in neighbors:
                node_data = G.nodes[neighbor]
                if node_data.get("type") == "file":
                    related.append({
                        "file_id": neighbor,
                        "filename": node_data.get("filename", ""),
                        "category": node_data.get("category", ""),
                        "tags": node_data.get("tags", []),
                        "relation": "direct"
                    })
            
            # 获取二度邻居
            if max_depth >= 2:
                for neighbor in neighbors:
                    second_neighbors = list(G.neighbors(neighbor))
                    for sn in second_neighbors:
                        if sn != file_id:
                            node_data = G.nodes[sn]
                            if node_data.get("type") == "file":
                                related.append({
                                    "file_id": sn,
                                    "filename": node_data.get("filename", ""),
                                    "category": node_data.get("category", ""),
                                    "tags": node_data.get("tags", []),
                                    "relation": "indirect"
                                })
        except nx.NetworkXError:
            pass
        
        return related
    
    def get_graph_stats(self) -> Dict:
        """获取知识图谱统计信息

        Returns:
            图谱统计字典，包含节点数、边数和类型分布
        """
        node_types = defaultdict(int)
        for node in self.graph["nodes"]:
            node_types[node.get("type", "unknown")] += 1
        
        edge_types = defaultdict(int)
        for edge in self.graph["edges"]:
            edge_types[edge.get("type", "unknown")] += 1
        
        return {
            "total_nodes": len(self.graph["nodes"]),
            "total_edges": len(self.graph["edges"]),
            "by_node_type": dict(node_types),
            "by_edge_type": dict(edge_types)
        }
    
    # ========== 综合统计 ==========
    
    def get_full_stats(self) -> Dict:
        """获取完整统计信息

        Returns:
            包含所有子系统统计的字典：metadata、versions、history、vectors、graph
        """
        files = list(self.metadata["files"].values())
        
        by_category = defaultdict(int)
        by_tag = defaultdict(int)
        
        for f in files:
            by_category[f.get("category", "uncategorized")] += 1
            for tag in f.get("tags", []):
                by_tag[tag] += 1
        
        total_size = sum(f.get("size", 0) for f in files)
        with_embedding = sum(1 for f in files if self.has_embedding(f["id"]))
        
        return {
            "metadata": {
                "total_files": len(files),
                "total_size": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "by_category": dict(by_category),
                "by_tag": dict(by_tag),
                "with_embedding": with_embedding
            },
            "versions": {
                "total_versions": len(self.versions["versions"])
            },
            "history": {
                "total_operations": len(self.history["operations"])
            },
            "vectors": {
                "total_embeddings": len(self.vectors["embeddings"])
            },
            "graph": self.get_graph_stats()
        }
    
    def print_stats(self) -> None:
        """打印统计信息到控制台"""
        stats = self.get_full_stats()
        
        print("\n📊 数据管理统计 v4.0")
        print("=" * 50)
        
        meta = stats["metadata"]
        print(f"总文件数：{meta['total_files']}")
        print(f"总大小：{meta['total_size_mb']:.2f} MB")
        print(f"已向量化：{meta['with_embedding']} 个文件")
        
        print("\n   按分类:")
        for cat, count in meta['by_category'].items():
            print(f"      {cat}: {count} 个")
        
        print("\n   按标签:")
        for tag, count in list(meta['by_tag'].items())[:10]:
            print(f"      {tag}: {count} 个")
        
        print(f"\n📚 版本管理:")
        print(f"   总版本数：{stats['versions']['total_versions']}")
        
        print(f"\n📜 操作历史:")
        print(f"   总操作数：{stats['history']['total_operations']}")
        
        print(f"\n🔗 向量数据:")
        print(f"   向量数量：{stats['vectors']['total_embeddings']}")
        
        print(f"\n🕸️ 知识图谱:")
        graph = stats["graph"]
        print(f"   节点数：{graph['total_nodes']}")
        print(f"   边数：{graph['total_edges']}")
        print(f"   分类节点：{graph['by_node_type'].get('category', 0)}")
        print(f"   标签节点：{graph['by_node_type'].get('tag', 0)}")


# CLI
if __name__ == "__main__":
    import sys
    
    dm = DataManager()
    
    if len(sys.argv) < 2:
        print("数据管理器 v4.0")
        print("\n用法:")
        print("  data_manager.py stats              # 查看统计")
        print("  data_manager.py add <file>         # 添加文件")
        print("  data_manager.py list               # 列出文件")
        print("  data_manager.py history [file_id]  # 查看历史")
        print("  data_manager.py graph <file_id>    # 查看图谱关联")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "stats":
        dm.print_stats()
    
    elif command == "add":
        if len(sys.argv) < 3:
            print("❌ 错误：请指定文件路径")
            sys.exit(1)
        
        filepath = sys.argv[2]
        try:
            file_id = dm.add_file_metadata(filepath)
            print(f"✅ 已添加文件")
            print(f"   文件 ID: {file_id}")
        except Exception as e:
            print(f"❌ {e}")
    
    elif command == "list":
        files = dm.list_files(limit=20)
        if files:
            print(f"📁 文件列表 ({len(files)} 个):")
            for f in files:
                print(f"   📄 {f['filename']} ({f['category']})")
                print(f"      ID: {f['id']}")
        else:
            print("❌ 没有文件")
    
    elif command == "history":
        file_id = sys.argv[2] if len(sys.argv) > 2 else None
        ops = dm.get_operation_history(file_id=file_id)
        if ops:
            print(f"📜 操作历史 ({len(ops)} 条):")
            for op in ops[:10]:
                print(f"   {op['timestamp'][:19]} - {op['operation']} ({op['file_id']})")
        else:
            print("❌ 没有历史记录")
    
    elif command == "graph":
        if len(sys.argv) < 3:
            print("❌ 错误：请指定文件 ID")
            sys.exit(1)
        
        file_id = sys.argv[2]
        related = dm.get_related_files(file_id)
        if related:
            print(f"🕸️ 相关文件 ({len(related)} 个):")
            for r in related:
                print(f"   📄 {r['filename']} ({r['relation']})")
        else:
            print("❌ 没有找到相关文件")
    
    else:
        print(f"❌ 未知命令：{command}")
