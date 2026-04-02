#!/bin/bash
# Agent File Cloud - 激活脚本

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 添加 site-packages 到 PYTHONPATH
export PYTHONPATH="$SKILL_DIR/site-packages:$PYTHONPATH"

echo "✅ Agent File Cloud 环境已激活"
echo "   目录：$SKILL_DIR"
echo "   PYTHONPATH: $PYTHONPATH"

# 如果需要切换到技能目录
cd "$SKILL_DIR"
