#!/bin/bash
# Agent File Cloud 技能使用脚本
# 用法：./use_skill.sh [command] [args]

SKILL_DIR="$HOME/.openclaw/skills/agent-file-cloud"
VENV_LIB="$SKILL_DIR/venv/lib/python3.11/site-packages"
export PYTHONPATH="$VENV_LIB:$PYTHONPATH"

cd "$SKILL_DIR"

case "$1" in
    "stats")
        echo "📊 数据管理统计"
        echo "=================="
        python3 data_manager.py stats
        echo ""
        echo "📊 检索推荐统计"
        echo "=================="
        python3 search_recommend.py stats
        ;;
    
    "add")
        shift
        python3 agent_file_cloud.py add "$@"
        ;;
    
    "search")
        shift
        python3 agent_file_cloud.py search "$@"
        ;;
    
    "list")
        python3 agent_file_cloud.py list "$@"
        ;;
    
    "recommend")
        shift
        python3 search_recommend.py recommend "$@"
        ;;
    
    "upload")
        shift
        python3 agent_file_cloud.py upload "$@"
        ;;
    
    "share")
        shift
        python3 agent_file_cloud.py share "$@"
        ;;
    
    "help"|*)
        echo "Agent File Cloud 技能使用帮助"
        echo "=============================="
        echo ""
        echo "用法：./use_skill.sh <command> [args]"
        echo ""
        echo "可用命令:"
        echo "  stats              - 查看统计"
        echo "  add <file>         - 添加文件"
        echo "  search <query>     - 搜索文件"
        echo "  list               - 列出文件"
        echo "  recommend <id>     - 推荐相似文件"
        echo "  upload <file>      - 上传到七牛云"
        echo "  share <id>         - 生成分享消息"
        echo "  help               - 显示帮助"
        echo ""
        echo "示例:"
        echo "  ./use_skill.sh add inbox/file.md --tags \"标签\" --desc \"描述\""
        echo "  ./use_skill.sh search \"财务报告\""
        echo "  ./use_skill.sh recommend file_xxx"
        echo "  ./use_skill.sh stats"
        ;;
esac
