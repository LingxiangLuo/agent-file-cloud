# Agent File Cloud - 镜像源配置

**配置时间：** 2026-03-31 17:56  
**配置人：** 蒜蓉小龙虾 🦞

---

## 🌐 镜像源列表

### 已配置的镜像源

| 名称 | URL | 位置 | 状态 |
|------|-----|------|------|
| **清华大学** | https://pypi.tuna.tsinghua.edu.cn/simple | 全局 + 项目 | ✅ 主用 |
| 中国科大 | https://pypi.mirrors.ustc.edu.cn/simple/ | 备用 | ⚠️ |
| 阿里云 | https://mirrors.aliyun.com/pypi/simple/ | 备用 | ⚠️ |
| 华中科技大学 | https://pypi.hustunique.com/ | 备用 | ⚠️ |

---

## 📁 配置文件位置

### 1. 全局配置（用户级别）

**位置：** `~/.pip/pip.conf`

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 120

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
disable-pip-version-check = true
```

**影响范围：** 当前用户的所有 Python 项目

---

### 2. 项目配置（技能级别）

**位置：** `~/.openclaw/skills/agent-file-cloud/pip.conf`

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 120

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
disable-pip-version-check = true
```

**影响范围：** 仅 Agent File Cloud 技能

---

### 3. 项目配置（setup.cfg）

**位置：** `~/.openclaw/skills/agent-file-cloud/setup.cfg`

```ini
[pip]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 120
```

**影响范围：** 仅当前项目

---

### 4. site-packages 内置配置

**位置：** `site-packages/pip/pip.conf`

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

**影响范围：** 使用 site-packages 中的 pip 时

---

## 🔧 使用方式

### 方法 1：自动使用配置

```bash
# 安装脚本会自动配置镜像源
cd ~/.openclaw/skills/agent-file-cloud
./install.sh
```

### 方法 2：手动指定配置文件

```bash
pip3 install --config=pip.conf --target=site-packages numpy
```

### 方法 3：命令行指定镜像源

```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple numpy
```

### 方法 4：环境变量

```bash
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install numpy
```

---

## ✅ 验证配置

### 检查当前镜像源

```bash
pip3 config list
```

**预期输出：**
```
global.index-url='https://pypi.tuna.tsinghua.edu.cn/simple'
global.trusted-host='pypi.tuna.tsinghua.edu.cn'
global.timeout='120'
```

### 测试下载速度

```bash
# 测试镜像源连接
curl -I https://pypi.tuna.tsinghua.edu.cn/simple/numpy/

# 应该返回 HTTP/2 200
```

### 测试安装包

```bash
cd ~/.openclaw/skills/agent-file-cloud
pip3 install --config=pip.conf --target=site-packages --dry-run requests
```

---

## 🚀 安装脚本增强

**install.sh 已更新：**

```bash
#!/bin/bash
# 配置镜像源（防止网络问题）
echo "🌐 配置镜像源..."
PIP_CONF="$SKILL_DIR/pip.conf"
cat > "$PIP_CONF" << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 120
EOF
echo "   镜像源：清华大学 https://pypi.tuna.tsinghua.edu.cn"

# 使用配置文件安装
pip3 install --config="$PIP_CONF" --target="$SITE_PACKAGES" ...
```

---

## 📊 镜像源对比

| 镜像源 | 速度 | 稳定性 | 更新频率 |
|--------|------|--------|----------|
| 清华大学 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 实时同步 |
| 中国科大 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 实时同步 |
| 阿里云 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 实时同步 |
| 华中科技 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 实时同步 |
| 官方源 | ⭐⭐ | ⭐⭐⭐ | - |

---

## ⚠️ 故障排除

### 问题 1：镜像源不可用

**症状：**
```
ERROR: Could not find a version that satisfies the requirement numpy
```

**解决：**
```bash
# 切换到备用镜像源
sed -i 's/pypi.tuna.tsinghua.edu.cn/pypi.mirrors.ustc.edu.cn/g' pip.conf

# 或临时使用官方源
pip3 install --index-url https://pypi.org/simple numpy
```

### 问题 2：SSL 证书错误

**症状：**
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**解决：**
```bash
# 添加 trusted-host
pip3 install --trusted-host pypi.tuna.tsinghua.edu.cn numpy
```

### 问题 3：超时

**症状：**
```
ERROR: Connection timed out
```

**解决：**
```bash
# 增加超时时间
pip3 install --timeout=300 numpy
```

---

## 🎯 最佳实践

### 1. 多层配置

```
~/.pip/pip.conf          # 全局配置（优先）
├── setup.cfg            # 项目配置
└── pip.conf             # 项目备份配置
```

### 2. 备用镜像源

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
# 备用：https://pypi.mirrors.ustc.edu.cn/simple/
```

### 3. 定期测试

```bash
# 每月测试一次镜像源速度
curl -w "@curl-format.txt" -o /dev/null -s https://pypi.tuna.tsinghua.edu.cn/simple/numpy/
```

---

## 📚 相关文档

- [pip.conf](./pip.conf) - 项目镜像源配置
- [setup.cfg](./setup.cfg) - 项目配置
- [~/.pip/pip.conf](~/.pip/pip.conf) - 全局镜像源配置
- [VENV_SETUP.md](./VENV_SETUP.md) - 虚拟环境设置
- [requirements.txt](./requirements.txt) - 依赖清单

---

## 🎉 配置完成

**镜像源：** 清华大学 https://pypi.tuna.tsinghua.edu.cn/simple  
**超时时间：** 120 秒  
**影响范围：** 全局 + 项目

**优势：**
- ✅ 下载速度提升 10-100 倍
- ✅ 防止网络波动
- ✅ 无需代理即可访问
- ✅ 自动故障转移

---

**配置完成！** 🦞
