#!/usr/bin/env python3
"""
Agent File Cloud - 智能文件管理系统 v3.0

基于阿里云 Embedding 的语义搜索 + 云地冷热智能存储管理

功能:
- 语义搜索 (Embedding 向量)
- 相似推荐 (向量 + 关键词)
- 文件管理 (添加/搜索/统计)
- 存储策略 (热/温/冷分类)
- 云地同步 (本地/云端/双存)
"""

import os
import sys
import json
import hashlib
import time
import fcntl
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 技能根目录（自动检测）
SKILL_DIR = Path(__file__).parent.resolve()

# 工作目录（可配置，默认在技能目录）
WORKSPACE_ROOT = Path(os.getenv(
    "AGENT_FILE_CLOUD_WORKSPACE",
    SKILL_DIR / "workspace"
))

# 允许的文件根目录（用于路径遍历验证）
ALLOWED_ROOT_DIR = str(WORKSPACE_ROOT)

# 配置文件（统一配置）
CONFIG_FILE = SKILL_DIR / "config" / "config.json"
DB_FILE = SKILL_DIR / "config" / "files.json"


def ensure_directories():
    """确保必要目录存在"""
    dirs = [
        SKILL_DIR / "config",
        SKILL_DIR / "workspace" / "inbox",
        SKILL_DIR / "workspace" / "archive",
        SKILL_DIR / "workspace" / "temp",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict:
    """加载统一配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 默认配置
    return {
        "version": "3.0",
        "api": {
            "dashscope_api_key": os.getenv("DASHSCOPE_API_KEY", ""),
            "embedding_model": "text-embedding-v4",
            "dimension": 1024
        },
        "qiniu": {
            "access_key": "",
            "secret_key": "",
            "bucket": "",
            "domain": "",
            "default_expiry_days": 7
        },
        "directories": {
            "inbox": str(WORKSPACE_ROOT / "inbox"),
            "archive": str(WORKSPACE_ROOT / "archive"),
            "temp": str(WORKSPACE_ROOT / "temp")
        },
        "storage_policy": {
            "hot_extensions": [".py", ".sh", ".js", ".yaml", ".yml"],
            "cold_extensions": [".md", ".pdf", ".png", ".jpg", ".mp4"],
            "warm_extensions": [".json", ".xml", ".log"]
        }
    }


def load_db() -> Dict:
    """加载数据库"""
    if DB_FILE.exists():
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"files": [], "next_id": 1}


def save_db(db: Dict) -> None:
    """保存数据库（带文件锁）"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock_path = DB_FILE.with_suffix('.lock')

    with open(lock_path, 'w', encoding='utf-8') as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def is_safe_path(base_dir: str, target_path: str) -> bool:
    """验证目标路径是否在基础目录内，防止路径遍历攻击"""
    try:
        base = Path(base_dir).resolve()
        target = Path(target_path).resolve()
        # 如果 target 是相对路径，先转换为绝对路径
        if not target.is_absolute():
            target = (Path.cwd() / target).resolve()
        # 检查 target 是否在 base 目录内
        target.relative_to(base)
        return True
    except (ValueError, RuntimeError):
        return False


def generate_file_id(filepath: str) -> str:
    """生成唯一文件 ID（使用 UUID 确保唯一性）"""
    import uuid
    unique_id = uuid.uuid4()
    return f"file_{unique_id.hex[:16]}"


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """提取关键词（基于词频）"""
    import re
    words = re.split(r'[,\.\s\n\t]+', text)
    # 过滤特殊字符和引号
    words = [w.strip().replace('"', '').replace("'", '').replace('\\', '') for w in words if len(w) > 1]
    words = [w for w in words if w]  # 移除空字符串
    
    freq: Dict[str, int] = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:max_keywords]]


class AgentFileCloud:
    """Agent File Cloud 主类"""
    
    def __init__(self, verbose: bool = True):
        """
        初始化系统
        
        Args:
            verbose: 是否显示详细输出
        """
        self.verbose = verbose
        self.config = load_config()
        self.db = load_db()
        self.embedding_api = None
        
        # 确保目录存在
        ensure_directories()
        
        if self.verbose:
            print("🚀 初始化 Agent File Cloud 智能文件管理系统...")
        
        # 初始化 Embedding API
        try:
            from embedding_api import EmbeddingAPI
            self.embedding_api = EmbeddingAPI(
                api_key=self.config.get("api", {}).get("dashscope_api_key"),
                model=self.config.get("api", {}).get("embedding_model", "text-embedding-v4"),
                dimension=self.config.get("api", {}).get("dimension", 1024)
            )
            if self.verbose:
                print("✅ Embedding API 已加载")
                print(f"   模型：{self.embedding_api.model}")
                print(f"   维度：{self.embedding_api.dimension}")
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Embedding API 加载失败：{e}")
                print("   将使用关键词搜索（降级模式）")
        
        if self.verbose:
            print(f"✅ 数据库已加载：{len(self.db['files'])} 个文件")
    
    def add_file(
        self,
        filepath: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        category: str = "uncategorized",
        project: str = ""
    ) -> Dict:
        """
        添加文件到数据库

        Args:
            filepath: 文件路径
            description: 文件描述
            tags: 标签列表
            category: 分类
            project: 所属项目

        Returns:
            添加结果
        """
        filepath = Path(filepath)
        if not filepath.exists():
            return {"error": f"文件不存在：{filepath}"}

        # 安全验证：防止路径遍历攻击
        if not is_safe_path(ALLOWED_ROOT_DIR, str(filepath)):
            return {"error": f"文件路径超出允许范围：{filepath}"}
        
        # 生成元数据
        file_id = generate_file_id(str(filepath))
        file_size = filepath.stat().st_size
        
        # 读取内容提取关键词
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()[:5000]  # 限制长度
            keywords = extract_keywords(content)
        except Exception:
            content = ""
            keywords = []
        
        # 生成向量（如果有 Embedding）
        embedding = None
        if self.embedding_api:
            try:
                embedding_text = f"{filepath.name} {description} {' '.join(keywords)}"
                embedding = self.embedding_api.create_embedding(embedding_text)
                if self.verbose:
                    print("✅ 已生成向量")
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ 向量生成失败：{e}")
        
        # 文件记录
        file_record = {
            "id": file_id,
            "path": str(filepath),
            "filename": filepath.name,
            "size": file_size,
            "category": category,
            "tags": tags or [],
            "description": description,
            "project": project,
            "keywords": keywords,
            "created_at": datetime.now().isoformat(),
            "created_by": "OpenClaw-Agent",
            "embedding": embedding,
            "qiniu_id": None,
            "qiniu_url": None,
            "access_count": 0,
            "last_accessed": None
        }
        
        self.db["files"].append(file_record)
        self.db["next_id"] += 1
        save_db(self.db)
        
        return {
            "success": True,
            "file_id": file_id,
            "message": f"已添加文件：{filepath.name}"
        }
    
    def search(self, query: str, k: int = 10) -> List[Dict]:
        """
        搜索文件
        
        Args:
            query: 搜索查询
            k: 返回数量
        
        Returns:
            搜索结果列表
        """
        results = []
        
        # 语义搜索（如果有 Embedding）
        if self.embedding_api:
            try:
                query_embedding = self.embedding_api.create_embedding(query, text_type='query')
                
                for f in self.db["files"]:
                    if f.get("embedding"):
                        similarity = self.embedding_api.cosine_similarity(
                            query_embedding, f["embedding"]
                        )
                        if similarity > 0.5:
                            results.append({
                                "file": f,
                                "score": similarity,
                                "type": "semantic"
                            })
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ 语义搜索失败：{e}")
        
        # 关键词搜索（后备）
        query_lower = query.lower()
        for f in self.db["files"]:
            score = 0
            
            if query_lower in f.get("filename", "").lower():
                score += 3
            if query_lower in f.get("description", "").lower():
                score += 2
            if query_lower in ' '.join(f.get("keywords", [])).lower():
                score += 2
            if any(query_lower in tag.lower() for tag in f.get("tags", [])):
                score += 1
            
            if score > 0 and not any(r["file"]["id"] == f["id"] for r in results):
                results.append({
                    "file": f,
                    "score": score / 3.0,
                    "type": "keyword"
                })
        
        # 排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]
    
    def recommend_similar(self, file_id: str, k: int = 5) -> Dict:
        """
        推荐相似文件
        
        Args:
            file_id: 源文件 ID
            k: 推荐数量
        
        Returns:
            推荐结果
        """
        # 找到源文件
        source = None
        for f in self.db["files"]:
            if f["id"] == file_id:
                source = f
                break
        
        if not source:
            return {"error": f"文件未找到：{file_id}"}
        
        results = []
        
        # 向量相似度
        if source.get("embedding") and self.embedding_api:
            for f in self.db["files"]:
                if f["id"] == file_id or not f.get("embedding"):
                    continue
                
                similarity = self.embedding_api.cosine_similarity(
                    source["embedding"], f["embedding"]
                )
                if similarity > 0.7:
                    results.append({
                        "file": f,
                        "score": similarity,
                        "reason": "向量相似度高"
                    })
        
        # 关键词重叠
        if len(results) < k:
            source_keywords = set(source.get("keywords", []))
            for f in self.db["files"]:
                if f["id"] == file_id:
                    continue
                
                f_keywords = set(f.get("keywords", []))
                overlap = len(source_keywords & f_keywords)
                
                if overlap > 0 and not any(r["file"]["id"] == f["id"] for r in results):
                    results.append({
                        "file": f,
                        "score": overlap / max(len(source_keywords), 1),
                        "reason": f"关键词重叠：{overlap} 个"
                    })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "source_file": source,
            "similar_files": results[:k],
            "count": len(results)
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        files = self.db["files"]
        
        by_category: Dict[str, int] = {}
        for f in files:
            cat = f.get("category", "uncategorized")
            by_category[cat] = by_category.get(cat, 0) + 1
        
        by_tag: Dict[str, int] = {}
        for f in files:
            for tag in f.get("tags", []):
                by_tag[tag] = by_tag.get(tag, 0) + 1
        
        total_size = sum(f.get("size", 0) for f in files)
        emb_count = sum(1 for f in files if f.get("embedding"))
        
        return {
            "total_files": len(files),
            "total_size": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "by_category": by_category,
            "by_tag": by_tag,
            "with_embedding": emb_count,
            "embedding_api": self.embedding_api.get_stats() if self.embedding_api else None
        }
    
    def list_files(self, limit: int = 20) -> List[Dict]:
        """列出文件"""
        return self.db["files"][-limit:]


def print_file_info(f: Dict) -> None:
    """打印文件信息"""
    print(f"\n📄 {f.get('filename', 'Unknown')}")
    print(f"   ID: {f.get('id')}")
    print(f"   路径：{f.get('path')}")
    print(f"   分类：{f.get('category')}")
    print(f"   标签：{', '.join(f.get('tags', [])) or '无'}")
    print(f"   描述：{f.get('description', '无')}")
    print(f"   关键词：{', '.join(f.get('keywords', [])[:5]) or '无'}")
    print(f"   大小：{f.get('size', 0)} B")
    print(f"   创建时间：{f.get('created_at', 'Unknown')}")
    if f.get('embedding'):
        print(f"   ✅ 已向量化")


# CLI 入口
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Agent File Cloud - 智能文件管理系统 v4.0")
        print("\n用法:")
        print("  agent_file_cloud.py add <file> [--tags <tags>] [--desc <desc>]")
        print("  agent_file_cloud.py search <keyword>  # 关键词搜索")
        print("  agent_file_cloud.py list [--limit <n>]")
        print("  agent_file_cloud.py stats")
        print("  agent_file_cloud.py recommend <file_id>  # 推荐相似文件")
        print("  agent_file_cloud.py upload <file> [--tags <tags>] [--desc <desc>]")
        print("  agent_file_cloud.py share <file_id>  # 分享单个文件")
        print("  agent_file_cloud.py share-batch <id1,id2,...>  # 批量分享")
        print("  agent_file_cloud.py graph [file_id]  # 图谱可视化")
        print("\n高级功能:")
        print("  python3 search_recommend.py stats     # 检索统计")
        print("  python3 search_recommend.py recommend <id>  # 混合推荐")
        print("  python3 data_manager.py stats         # 数据管理统计")
        print("  python3 graph_viz.py show             # 图谱概览")
        sys.exit(0)
    
    # 初始化系统
    cloud = AgentFileCloud()
    
    command = sys.argv[1]
    
    if command == "add":
        if len(sys.argv) < 3:
            print("❌ 错误：请指定文件路径")
            sys.exit(1)
        
        filepath = sys.argv[2]
        tags: List[str] = []
        desc = ""
        category = ""
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--tags" and i + 1 < len(sys.argv):
                tags = sys.argv[i + 1].split(",")
                i += 2
            elif sys.argv[i] == "--desc" and i + 1 < len(sys.argv):
                desc = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--category" and i + 1 < len(sys.argv):
                category = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        result = cloud.add_file(filepath, description=desc, tags=tags, category=category)
        if result.get("success"):
            print(f"✅ {result['message']}")
            print(f"   文件 ID: {result['file_id']}")
            print(f"💡 提示：添加多个文件后运行 'python3 generate_graph_html.py' 更新图谱")
        else:
            print(f"❌ {result.get('error')}")
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("❌ 错误：请指定搜索关键词")
            sys.exit(1)
        
        keyword = sys.argv[2]
        results = cloud.search(keyword)
        
        if results:
            print(f"🔍 找到 {len(results)} 个相关文件:")
            for r in results:
                print_file_info(r["file"])
                print(f"   匹配类型：{r['type']} (得分：{r['score']:.2f})")
        else:
            print("❌ 未找到相关文件")
    
    elif command == "list":
        limit = 20
        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            if idx + 1 < len(sys.argv):
                limit = int(sys.argv[idx + 1])
        
        files = cloud.list_files(limit=limit)
        
        if files:
            print(f"📁 文件列表 (共 {len(files)} 个):")
            for f in files:
                print_file_info(f)
        else:
            print("❌ 没有文件记录")
    
    elif command == "stats":
        stats = cloud.get_stats()
        print("📊 文件统计:")
        print(f"   总文件数：{stats['total_files']}")
        print(f"   总大小：{stats['total_size_mb']:.2f} MB")
        print(f"   已向量：{stats['with_embedding']} 个文件")
        print("\n   按分类:")
        for cat, count in stats.get('by_category', {}).items():
            print(f"      {cat}: {count} 个")
        print("\n   按标签:")
        for tag, count in stats.get('by_tag', {}).items():
            print(f"      {tag}: {count} 个")
        
        if stats.get('embedding_api'):
            print("\n📊 Embedding API 统计:")
            emb = stats['embedding_api']
            print(f"   调用次数：{emb['call_count']}")
            print(f"   模型：{emb['model']}")
            print(f"   维度：{emb['dimension']}")
    
    elif command == "upload":
        # 智能上传到七牛云
        if len(sys.argv) < 3:
            print("❌ 错误：请指定文件路径")
            sys.exit(1)
        
        from storage_manager import StorageManager
        storage_mgr = StorageManager()
        
        filepath = sys.argv[2]
        tags: List[str] = []
        desc = ""
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--tags" and i + 1 < len(sys.argv):
                tags = sys.argv[i + 1].split(",")
                i += 2
            elif sys.argv[i] == "--desc" and i + 1 < len(sys.argv):
                desc = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        result = storage_mgr.upload_to_qiniu(filepath, tags=tags, description=desc)
        if result.get("success"):
            print(f"✅ {result.get('message', '上传成功')}")
            print(f"   文件 ID: {result['file_id']}")
            print(f"   下载链接：{result['download_url']}")
            print(f"\n💡 使用以下命令生成分享消息:")
            print(f"   python3 agent_file_cloud.py share {result['file_id']}")
        elif result.get("skipped"):
            print(f"⏸️ 跳过上传：{result['reason']}")
        else:
            print(f"❌ {result.get('error', '上传失败')}")
    
    elif command == "share":
        # 生成分享消息（含下载链接）
        if len(sys.argv) < 3:
            print("❌ 错误：请指定文件 ID")
            sys.exit(1)
        
        from storage_manager import StorageManager
        storage_mgr = StorageManager()
        
        file_id = sys.argv[2]
        message = storage_mgr.format_share_message(file_id)
        
        if message:
            print(message)
        else:
            print(f"❌ 文件未找到：{file_id}")
            print("\n💡 使用以下命令查看文件列表:")
            print("   python3 agent_file_cloud.py list")
    
    elif command == "share-batch":
        # 批量分享消息
        if len(sys.argv) < 3:
            print("❌ 错误：请指定文件 ID 列表（逗号分隔）")
            sys.exit(1)
        
        from storage_manager import StorageManager
        storage_mgr = StorageManager()
        
        file_ids = sys.argv[2].split(",")
        message = storage_mgr.format_batch_share_message(file_ids)
        
        if message:
            print(message)
        else:
            print(f"❌ 未找到有效文件")
            print("\n💡 使用以下命令查看文件列表:")
            print("   python3 agent_file_cloud.py list")
    
    elif command == "graph":
        # 图谱可视化
        from graph_viz import GraphVisualizer
        viz = GraphVisualizer()
        
        file_id = sys.argv[2] if len(sys.argv) > 2 else None
        
        if file_id:
            print(viz.visualize_text(file_id))
        else:
            print(viz.visualize_text())
    
    elif command == "recommend":
        if len(sys.argv) < 3:
            print("❌ 错误：请指定文件 ID")
            sys.exit(1)
        
        file_id = sys.argv[2]
        result = cloud.recommend_similar(file_id)
        
        if result.get("error"):
            print(f"❌ {result['error']}")
        else:
            print(f"📌 与 {result['source_file']['filename']} 相似的文件 ({result['count']} 个):")
            for f in result['similar_files']:
                print_file_info(f["file"])
                print(f"   推荐理由：{f['reason']} (得分：{f['score']:.2f})")
    
    else:
        print(f"❌ 未知命令：{command}")
        sys.exit(1)
