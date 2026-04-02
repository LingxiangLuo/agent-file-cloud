#!/usr/bin/env python3
"""
自动清理过期文件并更新图谱

功能：
1. 检查过期文件
2. 从七牛云删除过期文件
3. 更新本地数据库
4. 自动重新生成图谱 HTML
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加 venv 路径
venv_paths = [
    Path(__file__).parent / "venv" / "lib" / "python3.11" / "site-packages",
    Path(__file__).parent / "venv" / "local" / "lib" / "python3.11" / "dist-packages",
]

for venv_path in venv_paths:
    if venv_path.exists():
        sys.path.insert(0, str(venv_path))
        break

try:
    import qiniu
    from qiniu import Auth, BucketManager
except ImportError as e:
    print(f"⚠️  七牛云 SDK 未安装：{e}")
    sys.exit(1)

# 技能目录
SKILL_DIR = Path(__file__).parent
CONFIG_FILE = SKILL_DIR / "config" / "config.json"
QINIU_HISTORY_FILE = SKILL_DIR / "config" / "qiniu_files.json"
METADATA_DB = SKILL_DIR / "config" / "metadata.json"


def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_qiniu_history():
    """加载七牛云历史"""
    if QINIU_HISTORY_FILE.exists():
        with open(QINIU_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"files": []}


def save_qiniu_history(history):
    """保存七牛云历史"""
    with open(QINIU_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def load_metadata():
    """加载元数据"""
    if METADATA_DB.exists():
        with open(METADATA_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"files": {}}


def save_metadata(metadata):
    """保存元数据"""
    with open(METADATA_DB, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def check_expired_files():
    """检查过期文件"""
    history = load_qiniu_history()
    now = datetime.now()
    
    expired = []
    active = []
    
    for file in history["files"]:
        if file.get("status") != "active":
            continue
        
        expiry_time = file.get("expiry_time")
        if expiry_time:
            expiry = datetime.fromisoformat(expiry_time)
            if expiry < now:
                expired.append(file)
            else:
                active.append(file)
        else:
            active.append(file)
    
    return expired, active


def delete_expired_files(expired_files):
    """删除过期文件"""
    config = load_config()
    qiniu_config = config.get("qiniu")
    
    if not qiniu_config:
        print("❌ 七牛云配置未设置")
        return False
    
    auth = Auth(qiniu_config['access_key'], qiniu_config['secret_key'])
    bucket = BucketManager(auth)
    
    deleted = []
    failed = []
    
    for file in expired_files:
        qiniu_key = file.get("qiniu_key")
        if not qiniu_key:
            failed.append({"file": file, "reason": "无 qiniu_key"})
            continue
        
        try:
            bucket.delete(qiniu_config['bucket'], qiniu_key)
            print(f"✅ 已删除：{file.get('filename')} ({qiniu_key})")
            deleted.append(file)
        except Exception as e:
            print(f"❌ 删除失败：{file.get('filename')} - {e}")
            failed.append({"file": file, "reason": str(e)})
    
    return deleted, failed


def update_history(active_files, deleted_files):
    """更新历史记录"""
    history = load_qiniu_history()
    
    # 标记已删除文件
    for file in deleted_files:
        file["status"] = "expired_deleted"
        file["deleted_at"] = datetime.now().isoformat()
    
    # 更新历史
    history["files"] = active_files + deleted_files
    save_qiniu_history(history)
    
    # 更新元数据
    metadata = load_metadata()
    deleted_ids = {f["file_id"] for f in deleted_files}
    
    for file_id in list(metadata["files"].keys()):
        file_data = metadata["files"][file_id]
        if file_data.get("qiniu_id") in deleted_ids:
            file_data["qiniu_url"] = None
            file_data["qiniu_status"] = "expired"
    
    save_metadata(metadata)


def regenerate_graph():
    """重新生成图谱"""
    print("\n🔄 重新生成图谱...")
    
    # 调用生成脚本
    import subprocess
    result = subprocess.run(
        [sys.executable, str(SKILL_DIR / "generate_graph_html.py")],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ 图谱已更新")
    else:
        print(f"❌ 图谱更新失败：{result.stderr}")


def main():
    """主函数"""
    print("🧹 自动清理过期文件")
    print("=" * 50)
    
    # 检查过期文件
    expired, active = check_expired_files()
    
    print(f"活跃文件：{len(active)}")
    print(f"过期文件：{len(expired)}")
    
    if not expired:
        print("\n✅ 无过期文件")
        return
    
    print(f"\n⏰ 准备删除 {len(expired)} 个过期文件...")
    
    # 删除过期文件
    deleted, failed = delete_expired_files(expired)
    
    print(f"\n删除成功：{len(deleted)}")
    print(f"删除失败：{len(failed)}")
    
    # 更新历史记录
    update_history(active, deleted)
    
    # 重新生成图谱
    if deleted:
        regenerate_graph()
    
    print("\n" + "=" * 50)
    print("✅ 清理完成！")


if __name__ == "__main__":
    main()
