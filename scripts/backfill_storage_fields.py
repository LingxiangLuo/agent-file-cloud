#!/usr/bin/env python3
"""
批量更新文件，添加存储类型字段
"""

import json
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
FILES_JSON = SKILL_DIR / "config" / "files.json"
CONFIG_JSON = SKILL_DIR / "config" / "config.json"


def backfill_storage_fields():
    """批量添加存储类型字段"""
    print("🔄 批量添加存储类型字段...\n")
    
    # 加载配置
    with open(CONFIG_JSON, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    hot_exts = set(config['storage_policy']['hot_extensions'])
    cold_exts = set(config['storage_policy']['cold_extensions'])
    # 移除重复项
    hot_exts = hot_exts - cold_exts
    
    # 加载文件
    with open(FILES_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    updated = 0
    for file in data['files']:
        ext = Path(file['filename']).suffix.lower()
        
        # 判断存储类型
        if ext in hot_exts:
            storage_type = 'hot'
        elif ext in cold_exts:
            storage_type = 'cold'
        else:
            storage_type = 'warm'
        
        # 判断存储位置
        storage_location = 'cloud' if file.get('qiniu_url') else 'local'
        
        # 更新字段
        if 'storage_type' not in file:
            file['storage_type'] = storage_type
            file['storage_location'] = storage_location
            updated += 1
    
    # 保存
    with open(FILES_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 更新完成!")
    print(f"   更新文件数：{updated}")
    print(f"   总文件数：{len(data['files'])}")
    
    # 统计分布
    stats = {'hot': 0, 'warm': 0, 'cold': 0}
    for f in data['files']:
        stats[f.get('storage_type', 'warm')] += 1
    
    print(f"\n📊 存储类型分布:")
    print(f"   🔥 热文件：{stats['hot']}")
    print(f"   ⚡ 温文件：{stats['warm']}")
    print(f"   ☁️ 冷文件：{stats['cold']}")


if __name__ == "__main__":
    backfill_storage_fields()
