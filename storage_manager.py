#!/usr/bin/env python3
"""
智能存储管理模块 v4.0

基于 DataManager 整合：
- 🔥 热文件：脚本/代码 → 本地存储 + 云端备份
- ☁️ 冷文件：文档/媒体 → 云端存储（用于传播）
- ⚡ 温文件：数据/其他 → 本地存储

依赖 DataManager 提供：
- 文件元数据管理
- 版本管理
- 历史记录
- 向量数据
- 知识图谱
"""

import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

try:
    import qiniu
    from qiniu import Auth, put_file_v2, BucketManager
except ImportError:
    qiniu = None  # 七牛云 SDK 未安装

# 导入 DataManager
from data_manager import DataManager


# 技能目录
SKILL_DIR = Path(__file__).parent
CONFIG_FILE = SKILL_DIR / "config" / "config.json"
DB_FILE = SKILL_DIR / "config" / "files.json"
QININIU_HISTORY_FILE = SKILL_DIR / "config" / "qiniu_files.json"

# 文件类型分类
FILE_CATEGORIES = {
    "hot_extensions": [
        '.py', '.sh', '.bash', '.js', '.ts', '.java', '.c', '.cpp',
        '.h', '.go', '.rs', '.rb', '.php', '.yaml', '.yml', '.toml',
        '.ini', '.conf', 'makefile', 'dockerfile'
    ],
    "cold_extensions": [
        '.md', '.txt', '.rst', '.doc', '.docx', '.pdf',
        '.ppt', '.pptx', '.xls', '.xlsx', '.csv',
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp',
        '.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav',
        '.zip', '.tar', '.gz', '.rar', '.7z', '.html'
    ],
    "warm_extensions": [
        '.json', '.xml', '.sql', '.db', '.sqlite', '.log',
        '.bak', '.backup', '.old', '.sample', '.template'
    ]
}

# 传播需求关键词
DISTRIBUTION_KEYWORDS = ["分享", "传播", "发布", "公开", "external", "public", "share", "发送", "链接"]


class StorageManager:
    """智能存储管理器 v4.0（基于 DataManager）"""
    
    def __init__(self):
        """初始化存储管理器"""
        self.dm = DataManager()  # 使用 DataManager
        self.config = self.dm.config
        self.qiniu_history = self._load_qiniu_history()
        self.categories = FILE_CATEGORIES
    
    def _load_qiniu_history(self) -> Dict:
        """加载七牛云上传历史"""
        qiniu_history_file = SKILL_DIR / "config" / "qiniu_files.json"
        if qiniu_history_file.exists():
            with open(qiniu_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"files": []}
    
    def _save_qiniu_history(self):
        """保存七牛云上传历史"""
        qiniu_history_file = SKILL_DIR / "config" / "qiniu_files.json"
        qiniu_history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(qiniu_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.qiniu_history, f, indent=2, ensure_ascii=False)
    
    def get_file_category(self, filepath: str) -> str:
        """判断文件类型：hot/warm/cold"""
        ext = Path(filepath).suffix.lower()
        filename = Path(filepath).name.lower()
        
        if ext in self.categories["hot_extensions"]:
            return "hot"
        if ext in self.categories["cold_extensions"]:
            return "cold"
        if filename in ['makefile', 'dockerfile', 'jenkinsfile']:
            return "hot"
        return "warm"
    
    def check_distribution_need(self, file_metadata: Dict) -> Tuple[bool, List[str]]:
        """
        检查文件是否有传播/分享需求
        
        Returns:
            (是否有传播需求，传播渠道列表)
        """
        tags = file_metadata.get("tags", [])
        channels = []
        
        # 检查标签
        for tag in tags:
            tag_lower = tag.lower()
            if any(k in tag_lower for k in DISTRIBUTION_KEYWORDS):
                channels.append("share")
                break
        
        # 检查描述
        description = file_metadata.get("description", "").lower()
        if any(k in description for k in DISTRIBUTION_KEYWORDS):
            channels.append("share")
        
        # 检查是否已有云端链接
        if file_metadata.get("qiniu_url"):
            channels.append("qiniu")
        
        has_need = len(channels) > 0
        return has_need, channels
    
    def should_upload_to_cloud(self, file_metadata: Dict) -> Tuple[bool, str]:
        """
        智能决策是否应该上传到云端
        
        Returns:
            (是否上传，原因)
        """
        filepath = file_metadata.get("path", "")
        file_type = self.get_file_category(filepath)
        has_distribution_need, _ = self.check_distribution_need(file_metadata)
        
        # ☁️ 冷文件：默认上传云端
        if file_type == "cold":
            if has_distribution_need:
                return True, "冷文件 + 传播需求，必须上传云端"
            else:
                return True, "冷文件，建议上传云端便于分享"
        
        # 🔥 热文件：本地执行，云端备份
        if file_type == "hot":
            return True, "热文件，需要云端备份"
        
        # ⚡ 温文件：根据情况
        if has_distribution_need:
            return True, "有传播需求，上传云端"
        else:
            return False, "温文件，无传播需求，本地存储"
    
    def upload_to_qiniu(self, filepath: str, tags: List[str] = None, 
                       description: str = "", expiry_days: int = None,
                       force_upload: bool = False) -> Dict:
        """
        智能上传文件到七牛云
        
        Args:
            filepath: 文件路径
            tags: 标签列表
            description: 描述
            expiry_days: 有效期（天），默认使用配置
            force_upload: 强制上传（跳过智能决策）
        
        Returns:
            上传结果，包含下载链接
        """
        filepath = Path(filepath)
        if not filepath.exists():
            return {"error": f"文件不存在：{filepath}", "download_url": None}
        
        # 检查七牛云配置
        qiniu_config = self.config.get("qiniu")
        if not qiniu_config:
            return {"error": "七牛云配置未设置", "download_url": None}
        
        if not qiniu_config.get("access_key") or not qiniu_config.get("secret_key"):
            return {"error": "七牛云密钥未配置", "download_url": None}
        
        # 检查 SDK
        if qiniu is None:
            return {"error": "七牛云 SDK 未安装 (pip3 install qiniu)", "download_url": None}
        
        # 先添加文件到 DataManager（如果还没有）
        file_hash = hashlib.md5(open(filepath, 'rb').read()).hexdigest()
        existing_file = None
        for fid, fdata in self.dm.metadata["files"].items():
            if fdata.get("file_hash") == file_hash:
                existing_file = fdata
                break
        
        if not existing_file:
            file_id = self.dm.add_file_metadata(
                str(filepath),
                tags=tags or [],
                description=description or ""
            )
            file_metadata = self.dm.get_file_metadata(file_id)
        else:
            file_id = existing_file["id"]
            file_metadata = existing_file
        
        # 智能决策（非强制模式）
        if not force_upload:
            should_upload, reason = self.should_upload_to_cloud(file_metadata)
            if not should_upload:
                return {
                    "skipped": True,
                    "reason": reason,
                    "download_url": None
                }
        
        # 检查重复文件
        with open(filepath, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        if not force_upload:
            existing = self._find_qiniu_duplicate(file_hash)
            if existing:
                return {
                    "success": True,
                    "reused": True,
                    "file_id": existing["file_id"],
                    "download_url": existing["download_url"],
                    "message": f"复用历史文件（{existing['upload_time'][:10]} 上传）",
                    "expiry_time": existing.get("expiry_time", "")
                }
        
        # 执行上传
        try:
            auth = Auth(qiniu_config['access_key'], qiniu_config['secret_key'])
            token = auth.upload_token(qiniu_config['bucket'])
            
            # 生成七牛云文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filepath.name
            qiniu_key = f"uploads/{timestamp}_{filename}"
            
            # 上传
            ret, info = put_file_v2(token, qiniu_key, str(filepath))
            if info.status_code != 200:
                return {
                    "error": f"上传失败：{info.error}",
                    "download_url": None
                }
            
            # 生成下载链接（公开空间，无需签名）
            domain = qiniu_config['domain'].rstrip('/')
            if expiry_days is None:
                expiry_days = qiniu_config.get("default_expiry_days", 7)
            
            # 公开空间直接返回 URL，不需要签名
            download_url = f"{domain}/{qiniu_key}"
            
            # 记录历史
            now = datetime.now()
            record = {
                "file_id": self._generate_qiniu_id(filename),
                "filename": filename,
                "original_path": str(filepath),
                "qiniu_key": qiniu_key,
                "download_url": download_url,
                "upload_time": now.isoformat(),
                "expiry_time": (now + timedelta(days=expiry_days)).isoformat(),
                "expiry_days": expiry_days,
                "tags": tags or [],
                "description": description,
                "file_hash": file_hash,
                "file_size": filepath.stat().st_size,
                "status": "active"
            }
            
            self.qiniu_history["files"].append(record)
            self._save_qiniu_history()
            
            # 更新本地数据库
            self._update_local_db(filepath, record)
            
            return {
                "success": True,
                "file_id": record["file_id"],
                "filename": filename,
                "download_url": download_url,
                "expiry_time": record["expiry_time"],
                "message": f"✅ 已上传到七牛云，有效期{expiry_days}天"
            }
            
        except Exception as e:
            return {
                "error": f"上传异常：{str(e)}",
                "download_url": None
            }
    
    def _find_qiniu_duplicate(self, file_hash: str) -> Optional[Dict]:
        """查找七牛云中的重复文件"""
        for f in self.qiniu_history["files"]:
            if f.get("file_hash") == file_hash and f["status"] == "active":
                return f
        return None
    
    def _update_local_db(self, filepath: Path, qiniu_record: Dict):
        """更新本地数据库，添加七牛云信息"""
        for f in self.db["files"]:
            if f["path"] == str(filepath):
                f["qiniu_id"] = qiniu_record["file_id"]
                f["qiniu_url"] = qiniu_record["download_url"]
                f["qiniu_expiry"] = qiniu_record["expiry_time"]
                break
        
        # 保存数据库
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=2, ensure_ascii=False)
    
    def _generate_qiniu_id(self, filename: str) -> str:
        """生成七牛云文件 ID"""
        timestamp = str(int(time.time() * 1000))
        unique = hashlib.md5(f"{filename}{timestamp}".encode()).hexdigest()[:8]
        return f"qiniu_{timestamp}_{unique}"
    
    def get_download_url(self, file_id: str) -> Optional[str]:
        """获取文件的下载链接"""
        # 在七牛云历史中查找
        for f in self.qiniu_history["files"]:
            if f["file_id"] == file_id:
                return f["download_url"]
        
        # 在本地数据库中查找
        for f in self.db["files"]:
            if f.get("qiniu_id") == file_id:
                return f.get("qiniu_url")
        
        return None
    
    def format_share_message(self, file_id: str) -> Optional[str]:
        """
        生成分享给用户的消息（表格格式）
        
        Returns:
            格式化的分享消息（表格版）
        """
        return self.format_batch_share_message([file_id])
    
    def format_batch_share_message(self, file_ids: List[str]) -> Optional[str]:
        """
        生成批量分享消息（表格格式，统一单个和多个文件）
        
        Args:
            file_ids: 文件 ID 列表
        
        Returns:
            格式化的批量分享消息（表格版）
        """
        if not file_ids:
            return None
        
        files_info = []
        total_size = 0
        
        for file_id in file_ids:
            file_info = None
            for f in self.qiniu_history["files"]:
                if f["file_id"] == file_id:
                    file_info = f
                    break
            
            if not file_info:
                for f in self.dm.metadata["files"].values():
                    if f.get("qiniu_id") == file_id or f["id"] == file_id:
                        file_info = f
                        break
            
            if file_info:
                files_info.append(file_info)
                total_size += file_info.get("size", 0)
        
        if not files_info:
            return None
        
        # 格式化总大小
        if total_size >= 1024 * 1024:
            total_size_str = f"{total_size / (1024 * 1024):.1f} MB"
        elif total_size >= 1024:
            total_size_str = f"{total_size / 1024:.1f} KB"
        else:
            total_size_str = f"{total_size} B"
        
        # 生成表格头部
        if len(files_info) == 1:
            message = "📎 **文件分享**\n\n"
        else:
            message = f"📎 **批量文件分享**（共 {len(files_info)} 个文件，{total_size_str}）\n\n"
        
        # 生成表格
        message += "| # | 文件名 | 大小 | 描述 | 标签 | 有效期 | 下载 |\n"
        message += "|---|--------|------|------|------|--------|------|\n"
        
        # 添加文件行
        for i, file_info in enumerate(files_info, 1):
            filename = file_info.get("filename", "未知文件")
            file_size = file_info.get("size", 0)
            description = file_info.get("description", "")
            tags = file_info.get("tags", [])
            download_url = file_info.get("download_url", file_info.get("qiniu_url"))
            expiry = file_info.get("expiry_time", "")
            
            # 格式化文件大小
            if file_size >= 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            elif file_size >= 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size} B"
            
            # 格式化到期时间（公开空间永久有效）
            expiry_date = "永久"
            
            # 截断长描述
            if description and len(description) > 20:
                description = description[:17] + "..."
            
            # 截断长标签
            tags_str = ', '.join(tags) if tags else '无'
            if len(tags_str) > 20:
                tags_str = tags_str[:17] + "..."
            
            # 截断长文件名
            if len(filename) > 25:
                filename = filename[:22] + "..."
            
            message += f"| {i} | {filename} | {size_str} | {description or '无'} | {tags_str} | {expiry_date} | [📥]({download_url}) |\n"
        
        message += "\n> 💡 链接失效请联系我重新上传\n"
        
        return message
    
    def analyze_file(self, file_record: Dict) -> Dict:
        """分析单个文件的存储策略"""
        filepath = file_record.get("path", "")
        filename = file_record.get("filename", "")
        file_type = self.get_file_category(filepath)
        has_distribution_need, channels = self.check_distribution_need(file_record)
        should_upload, reason = self.should_upload_to_cloud(file_record)
        
        # 检查云端状态
        has_cloud_copy = file_record.get("qiniu_url") is not None
        download_url = file_record.get("qiniu_url")
        
        # 文件存在性
        file_exists = Path(filepath).exists()
        
        # 当前位置
        if file_exists and has_cloud_copy:
            current_location = "both"
        elif has_cloud_copy:
            current_location = "cloud"
        elif file_exists:
            current_location = "local"
        else:
            current_location = "unknown"
        
        # 推荐位置
        if file_type == "hot":
            recommended_location = "both"
        elif file_type == "cold":
            recommended_location = "cloud"
        else:
            recommended_location = "local" if not has_distribution_need else "cloud"
        
        # 操作建议
        action_required = "none"
        if should_upload and not has_cloud_copy:
            action_required = "upload_to_cloud"
        elif not file_exists and has_cloud_copy:
            action_required = "download_if_needed"
        
        return {
            "file_id": file_record.get("id"),
            "filename": filename,
            "filepath": filepath,
            "file_type": file_type,
            "current_location": current_location,
            "recommended_location": recommended_location,
            "has_distribution_need": has_distribution_need,
            "distribution_channels": channels,
            "should_upload_to_cloud": should_upload,
            "upload_reason": reason,
            "has_cloud_copy": has_cloud_copy,
            "download_url": download_url,
            "action_required": action_required,
            "file_exists": file_exists
        }
    
    def analyze_all_files(self) -> List[Dict]:
        """分析所有文件"""
        return [self.analyze_file(f) for f in self.db.get("files", [])]
    
    def get_storage_stats(self) -> Dict:
        """获取存储统计"""
        analyses = self.analyze_all_files()
        
        stats = {
            "total_files": len(analyses),
            "total_size": sum(
                next((f.get("size", 0) for f in self.db["files"] 
                      if f.get("id") == a["file_id"]), 0)
                for a in analyses
            ),
            "by_type": {"hot": 0, "warm": 0, "cold": 0},
            "by_location": {"local": 0, "cloud": 0, "both": 0, "unknown": 0},
            "recommended": {"local": 0, "cloud": 0, "both": 0},
            "actions": {"none": 0, "upload_to_cloud": 0, "download_if_needed": 0},
            "distribution_ready": 0,
            "with_cloud_copy": 0
        }
        
        for a in analyses:
            stats["by_type"][a["file_type"]] += 1
            stats["by_location"][a["current_location"]] = stats["by_location"].get(a["current_location"], 0) + 1
            stats["recommended"][a["recommended_location"]] = stats["recommended"].get(a["recommended_location"], 0) + 1
            stats["actions"][a["action_required"]] = stats["actions"].get(a["action_required"], 0) + 1
            
            if a["has_distribution_need"]:
                stats["distribution_ready"] += 1
            if a["has_cloud_copy"]:
                stats["with_cloud_copy"] += 1
        
        stats["total_size_mb"] = stats["total_size"] / (1024 * 1024)
        stats["total_size_gb"] = stats["total_size"] / (1024 ** 3)
        
        # 七牛云统计
        qiniu_stats = {
            "total_uploaded": len(self.qiniu_history["files"]),
            "active_files": sum(1 for f in self.qiniu_history["files"] if f["status"] == "active")
        }
        
        return {
            **stats,
            "qiniu": qiniu_stats
        }
    
    def print_stats(self):
        """打印存储统计"""
        stats = self.get_storage_stats()
        
        print("\n📊 智能存储统计 v3.0")
        print("=" * 50)
        print(f"总文件数：{stats['total_files']}")
        print(f"总大小：{stats['total_size_mb']:.2f} MB")
        
        print("\n📁 文件类型分布:")
        print(f"   🔥 热文件 (脚本/代码): {stats['by_type']['hot']} 个")
        print(f"   ⚡ 温文件 (数据/其他): {stats['by_type']['warm']} 个")
        print(f"   ☁️ 冷文件 (文档/传播): {stats['by_type']['cold']} 个")
        
        print("\n💾 存储分布:")
        print(f"   💻 仅本地：{stats['by_location']['local']} 个")
        print(f"   ☁️ 仅云端：{stats['by_location']['cloud']} 个")
        print(f"   🔄 云地双存：{stats['by_location']['both']} 个")
        
        print("\n📤 分享就绪:")
        print(f"   可分享文件：{stats['distribution_ready']} 个")
        print(f"   已上传云端：{stats['with_cloud_copy']} 个")
        
        print("\n☁️ 七牛云统计:")
        print(f"   总上传：{stats['qiniu']['total_uploaded']} 个")
        print(f"   活跃文件：{stats['qiniu']['active_files']} 个")
        
        # 需要操作的文件
        actions = [a for a in self.analyze_all_files() if a["action_required"] != "none"]
        if actions:
            print(f"\n⚠️ 需要处理 ({len(actions)} 个):")
            for a in actions[:5]:
                emoji = "⬆️" if a["action_required"] == "upload_to_cloud" else "⬇️"
                print(f"   {emoji} {a['filename']}: {a['action_required']}")
                if a.get('upload_reason'):
                    print(f"      原因：{a['upload_reason']}")
        else:
            print("\n✅ 存储状态已优化")


# CLI
if __name__ == "__main__":
    import sys
    
    manager = StorageManager()
    
    if len(sys.argv) < 2:
        print("智能存储管理 v3.0")
        print("\n用法:")
        print("  storage_manager.py stats          # 查看统计")
        print("  storage_manager.py analyze        # 分析所有文件")
        print("  storage_manager.py upload <file>  # 智能上传")
        print("  storage_manager.py share <id>     # 生成分享消息")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "stats":
        manager.print_stats()
    
    elif command == "analyze":
        for a in manager.analyze_all_files():
            print(f"\n📄 {a['filename']}")
            print(f"   类型：{a['file_type']} (🔥热/⚡温/☁️冷)")
            print(f"   当前：{a['current_location']}")
            print(f"   推荐：{a['recommended_location']}")
            print(f"   分享需求：{'是' if a['has_distribution_need'] else '否'}")
            print(f"   应上传云端：{'是' if a['should_upload_to_cloud'] else '否'}")
            if a.get('upload_reason'):
                print(f"   原因：{a['upload_reason']}")
            print(f"   下载链接：{'有' if a['download_url'] else '无'}")
    
    elif command == "upload":
        if len(sys.argv) < 3:
            print("❌ 错误：请指定文件路径")
            sys.exit(1)
        
        filepath = sys.argv[2]
        tags = []
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
        
        result = manager.upload_to_qiniu(filepath, tags=tags, description=desc)
        if result.get("success"):
            print(f"✅ {result.get('message', '上传成功')}")
            print(f"   文件 ID: {result['file_id']}")
            print(f"   下载链接：{result['download_url']}")
        elif result.get("skipped"):
            print(f"⏸️ 跳过上传：{result['reason']}")
        else:
            print(f"❌ {result.get('error', '上传失败')}")
    
    elif command == "share":
        if len(sys.argv) < 3:
            print("❌ 错误：请指定文件 ID")
            sys.exit(1)
        
        file_id = sys.argv[2]
        message = manager.format_share_message(file_id)
        
        if message:
            print(message)
        else:
            print(f"❌ 文件未找到：{file_id}")
    
    else:
        print(f"❌ 未知命令：{command}")
