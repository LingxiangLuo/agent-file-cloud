#!/bin/bash
# Agent File Cloud 技能安装脚本
# 用法：./install.sh

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$SKILL_DIR/workspace"
CONFIG_DIR="$SKILL_DIR/config"

echo "============================================================"
echo "🚀 Agent File Cloud 技能安装"
echo "============================================================"
echo ""

# 1. 创建目录
echo "📁 步骤 1/4: 创建必要目录..."
mkdir -p "$WORKSPACE_DIR/inbox"
mkdir -p "$WORKSPACE_DIR/archive"
mkdir -p "$WORKSPACE_DIR/temp"
mkdir -p "$CONFIG_DIR"
echo "✅ 目录已创建"
echo ""

# 2. 创建配置文件
echo "📝 步骤 2/4: 创建配置文件..."
CONFIG_FILE="$CONFIG_DIR/config.json"

if [ -f "$CONFIG_FILE" ]; then
    echo "⚠️  配置文件已存在，跳过创建"
else
    cat > "$CONFIG_FILE" << 'EOF'
{
  "version": "3.0",
  "api": {
    "dashscope_api_key": "",
    "embedding_model": "text-embedding-v4",
    "dimension": 1024
  },
  "directories": {
    "inbox": "/home/node/.openclaw/skills/agent-file-cloud/workspace/inbox",
    "archive": "/home/node/.openclaw/skills/agent-file-cloud/workspace/archive",
    "temp": "/home/node/.openclaw/skills/agent-file-cloud/workspace/temp"
  },
  "storage_policy": {
    "hot_extensions": [".py", ".sh", ".js", ".yaml", ".yml"],
    "cold_extensions": [".md", ".pdf", ".png", ".jpg", ".mp4"],
    "warm_extensions": [".json", ".xml", ".log"]
  }
}
EOF
    echo "✅ 配置文件已创建：$CONFIG_FILE"
    echo "⚠️  请编辑配置文件，设置您的 DASHSCOPE_API_KEY"
fi
echo ""

# 3. 安装依赖
echo "📦 步骤 3/4: 安装 Python 依赖..."

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误：pip3 未安装"
    exit 1
fi

# 安装依赖
pip3 install --break-system-packages \
    dashscope \
    faiss-cpu \
    numpy \
    networkx \
    openai \
    -q

echo "✅ 依赖已安装"
echo ""

# 4. 测试安装
echo "🔍 步骤 4/4: 测试安装..."

python3 -c "
import sys
sys.path.insert(0, '$SKILL_DIR')

try:
    import dashscope
    import faiss
    import numpy
    print('✅ 核心依赖加载成功')
except Exception as e:
    print(f'❌ 依赖加载失败：{e}')
    sys.exit(1)

try:
    from embedding_api import EmbeddingAPI
    print('✅ Embedding API 加载成功')
except Exception as e:
    print(f'⚠️  Embedding API 加载失败：{e}')
    print('   将使用关键词搜索（降级模式）')
"

echo ""
echo "============================================================"
echo "✅ 安装完成！"
echo "============================================================"
echo ""
echo "📁 安装位置：$SKILL_DIR"
echo "📂 工作目录：$WORKSPACE_DIR"
echo "📝 配置文件：$CONFIG_FILE"
echo ""
echo "下一步:"
echo "1. 编辑配置文件，设置 DASHSCOPE_API_KEY"
echo "2. 运行测试：python3 agent_file_cloud.py stats"
echo ""
echo "使用方法:"
echo "  python3 agent_file_cloud.py add <file> --tags \"标签\" --desc \"描述\""
echo "  python3 agent_file_cloud.py search \"关键词\""
echo "  python3 agent_file_cloud.py stats"
echo ""
