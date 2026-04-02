#!/usr/bin/env python3
"""
测试脚本 - 通过主程序添加文件
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agent_file_cloud import AgentFileCloud

# 初始化
cloud = AgentFileCloud(verbose=True)

# 扫描 inbox 目录
from pathlib import Path
inbox = Path('workspace/inbox')

if not inbox.exists():
    print(f"❌ inbox 目录不存在：{inbox}")
    sys.exit(1)

files = list(inbox.iterdir())
print(f"📁 找到 {len(files)} 个文件")

# 逐个添加
for i, filepath in enumerate(files, 1):
    if filepath.is_file() and not filepath.name.startswith('.'):
        print(f"\n[{i}/{len(files)}] 添加：{filepath.name}")
        
        # 根据文件名推断分类
        name = filepath.name.lower()
        if name.endswith(('.py', '.js', '.ts')):
            category = 'code'
        elif name.endswith(('.md', '.txt')):
            category = 'document'
        elif name.endswith(('.csv', '.json')):
            category = 'data'
        else:
            category = 'uncategorized'
        
        # 添加文件
        result = cloud.add_file(
            str(filepath),
            description=f"测试文件：{filepath.name}",
            tags=['test', category],
            category=category
        )
        
        if 'error' in result:
            print(f"  ❌ 错误：{result['error']}")
        else:
            print(f"  ✅ ID: {result.get('file_id')}")

# 显示统计
print("\n" + "=" * 50)
stats = cloud.get_stats()
print(f"📊 统计：{stats}")

# 生成图谱
print("\n" + "=" * 50)
print("🕸️  生成图谱...")
import subprocess
subprocess.run(['python3', 'generate_graph_html.py'])
