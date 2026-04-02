#!/usr/bin/env python3
"""
重建七牛云上传历史
从 files.json 中提取已上传的文件记录
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
FILES_JSON = SKILL_DIR / "config" / "files.json"
QINIU_HISTORY = SKILL_DIR / "config" / "qiniu_files.json"


def rebuild_qiniu_history():
    """重建七牛云上传历史"""
    print("🔄 重建七牛云上传历史...\n")
    
    # 加载 files.json
    if not FILES_JSON.exists():
        print("❌ files.json 不存在")
        return
    
    with open(FILES_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取有 qiniu_url 的文件
    qiniu_files = {"files": [], "version": "1.0", "rebuilt_at": datetime.now().isoformat()}
    
    for file in data['files']:
        if file.get('qiniu_url'):
            # 从 URL 提取 key
            qiniu_url = file['qiniu_url']
            qiniu_key = qiniu_url.split('/')[-1] if '/' in qiniu_url else qiniu_url
            
            record = {
                "file_id": file['id'],
                "filename": file['filename'],
                "original_path": file.get('path', ''),
                "qiniu_key": qiniu_key,
                "download_url": qiniu_url,
                "upload_time": file.get('created_at', datetime.now().isoformat()),
                "expiry_time": (datetime.now() + timedelta(days=7)).isoformat(),
                "expiry_days": 7,
                "tags": file.get('tags', []),
                "description": file.get('description', ''),
                "file_hash": file.get('file_hash', ''),
                "file_size": file.get('size', 0),
                "status": "active"
            }
            qiniu_files['files'].append(record)
    
    # 保存
    with open(QINIU_HISTORY, 'w', encoding='utf-8') as f:
        json.dump(qiniu_files, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 重建完成!")
    print(f"   文件数：{len(qiniu_files['files'])}")
    print(f"   保存位置：{QINIU_HISTORY}")
    
    # 显示前 5 个
    if qiniu_files['files']:
        print(f"\n📋 前 5 个记录:")
        for f in qiniu_files['files'][:5]:
            print(f"   - {f['filename']}: {f['download_url'][:50]}...")


if __name__ == "__main__":
    rebuild_qiniu_history()
