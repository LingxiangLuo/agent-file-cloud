#!/bin/bash
# Agent File Cloud 自动清理和更新
# 添加到 crontab：0 */6 * * * /path/to/auto_update.sh

cd /home/node/.openclaw/skills/agent-file-cloud

echo "🕐 自动清理任务 - $(date)" >> /tmp/agent_file_cloud_cleanup.log

# 运行清理脚本
python3 auto_cleanup.py >> /tmp/agent_file_cloud_cleanup.log 2>&1

# 如果清理脚本成功，重新生成图谱
if [ $? -eq 0 ]; then
    echo "✅ 清理完成" >> /tmp/agent_file_cloud_cleanup.log
else
    echo "❌ 清理失败" >> /tmp/agent_file_cloud_cleanup.log
fi

echo "---" >> /tmp/agent_file_cloud_cleanup.log
