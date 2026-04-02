# Agent File Cloud - 虚拟环境设置

**设置时间：** 2026-03-31 17:55  
**设置人：** 蒜蓉小龙虾 🦞

---

## 📦 依赖安装方式

### 方式 1：本地 site-packages（已采用）✅

**位置：** `~/.openclaw/skills/agent-file-cloud/site-packages/`

**优点：**
- ✅ 无需系统权限
- ✅ 依赖隔离在技能目录内
- ✅ 不影响系统 Python
- ✅ 多个技能可以有不同依赖版本

**安装命令：**
```bash
cd ~/.openclaw/skills/agent-file-cloud
pip3 install --target=site-packages numpy qiniu networkx faiss-cpu
```

**使用方式：**
```bash
# 方法 1：激活脚本
source activate_skill.sh

# 方法 2：设置 PYTHONPATH
export PYTHONPATH="$PWD/site-packages:$PYTHONPATH"

# 方法 3：Python 中动态添加
import sys
sys.path.insert(0, 'site-packages')
```

**已安装依赖：**
```
✅ numpy: 2.4.4
✅ qiniu: 7.17.0
✅ networkx: 3.6.1
✅ faiss: 1.13.0
```

---

### 方式 2：虚拟环境（推荐但需要权限）

**位置：** `~/.openclaw/skills/agent-file-cloud/venv/`

**创建命令：**
```bash
cd ~/.openclaw/skills/agent-file-cloud
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**问题：** 需要 `python3.11-venv` 包，当前系统未安装

---

### 方式 3：系统全局安装（不推荐）

```bash
pip3 install --break-system-packages -r requirements.txt
```

**缺点：**
- ❌ 污染系统 Python
- ❌ 需要 root 权限
- ❌ 可能与其他包冲突

---

## 🔧 当前配置

### site-packages 路径

```
/home/node/.openclaw/skills/agent-file-cloud/site-packages/
├── numpy/
├── qiniu/
├── networkx/
├── faiss/
├── requests/
└── ...
```

### 自动加载机制

**agent_file_cloud.py 启动时自动添加：**
```python
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.resolve()
SITE_PACKAGES = SKILL_DIR / "site-packages"

if SITE_PACKAGES.exists():
    sys.path.insert(0, str(SITE_PACKAGES))
```

---

## 📝 更新依赖

### 添加新依赖

```bash
cd ~/.openclaw/skills/agent-file-cloud
pip3 install --target=site-packages <package-name>
```

### 更新现有依赖

```bash
pip3 install --target=site-packages --upgrade <package-name>
```

### 重新安装所有依赖

```bash
rm -rf site-packages/*
pip3 install --target=site-packages -r requirements.txt
```

---

## 🧪 验证安装

```bash
cd ~/.openclaw/skills/agent-file-cloud

# 方法 1：使用激活脚本
source activate_skill.sh
python3 -c "import numpy; print(numpy.__version__)"

# 方法 2：直接运行
python3 -c "
import sys
sys.path.insert(0, 'site-packages')
import numpy, qiniu, networkx, faiss
print(f'numpy: {numpy.__version__}')
print(f'qiniu: {qiniu.__version__}')
print(f'networkx: {networkx.__version__}')
print(f'faiss: {faiss.__version__}')
"

# 方法 3：运行依赖检查
python3 scripts/check_dependencies.py
```

---

## 📊 依赖版本

| 包名 | 版本 | 用途 |
|------|------|------|
| numpy | 2.4.4 | 向量计算 |
| qiniu | 7.17.0 | 七牛云上传 |
| networkx | 3.6.1 | 图谱分析 |
| faiss-cpu | 1.13.2 | 向量索引 |
| requests | 2.33.1 | HTTP 请求 |
| certifi | 2026.2.25 | SSL 证书 |

---

## 🎯 最佳实践

### 1. 使用激活脚本

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias afc='cd ~/.openclaw/skills/agent-file-cloud && source activate_skill.sh'

# 使用
afc
python3 agent_file_cloud.py search "关键词"
```

### 2. 在代码中自动加载

```python
# agent_file_cloud.py 开头
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.resolve()
SITE_PACKAGES = SKILL_DIR / "site-packages"

if SITE_PACKAGES.exists():
    sys.path.insert(0, str(SITE_PACKAGES))
```

### 3. 定期更新依赖

```bash
# 每月更新一次
pip3 install --target=site-packages --upgrade -r requirements.txt
```

---

## ⚠️ 注意事项

### 1. site-packages 很大

```bash
# 查看大小
du -sh site-packages/
# 约 50-100MB
```

### 2. 不要提交到 git

```bash
# .gitignore
site-packages/
*.pyc
__pycache__/
```

### 3. 权限问题

如果遇到权限错误：
```bash
# 确保目录属于当前用户
chown -R $USER:$USER site-packages/
```

---

## 📚 相关文档

- [requirements.txt](./requirements.txt) - 依赖清单
- [activate_skill.sh](./activate_skill.sh) - 激活脚本
- [install.sh](./install.sh) - 完整安装脚本
- [DEPENDENCY_FIX_SUMMARY.md](./DEPENDENCY_FIX_SUMMARY.md) - 依赖修复总结

---

**设置完成！** 🎉

依赖已安装到 `site-packages/`，可以直接使用！
