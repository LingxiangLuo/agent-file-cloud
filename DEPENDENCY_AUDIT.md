# Agent File Cloud 依赖审查报告

**审查时间：** 2026-03-31 17:50  
**审查人：** 蒜蓉小龙虾 🦞

---

## 📦 依赖清单

### 核心依赖

| 包名 | 版本 | 用途 | 必需 | 状态 |
|------|------|------|------|------|
| **numpy** | ≥1.24.0 | 向量相似度计算 | ✅ 是 | ❌ 未安装 |
| **qiniu** | ≥7.17.0 | 七牛云上传 | ⚠️ 可选 | ❌ 未安装 |
| **networkx** | ≥3.0 | 图谱分析 | ❌ 否 | ❌ 未安装 |
| **dashscope** | ≥1.0.0 | 阿里云 SDK | ❌ 否 | ❌ 未安装 |
| **faiss-cpu** | ≥1.7.0 | 向量索引加速 | ❌ 否 | ❌ 未安装 |
| **openai** | ≥1.0.0 | OpenAI 兼容 API | ❌ 否 | ❌ 未安装 |

---

## 🔍 实际使用情况

### 代码中的导入方式

#### 1. numpy（embedding_api.py）

```python
def cosine_similarity(self, vec1, vec2):
    import numpy as np  # 运行时导入
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    # ...
```

**问题：**
- ❌ 运行时才导入，失败时无降级方案
- ❌ 无 `try-except` 保护
- ⚠️ 如果 numpy 未安装，`cosine_similarity()` 会崩溃

**建议：**
```python
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

def cosine_similarity(self, vec1, vec2):
    if not HAS_NUMPY:
        # 降级到纯 Python 实现
        return self._pure_python_similarity(vec1, vec2)
    # ...
```

---

#### 2. networkx（data_manager.py）

```python
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
```

**✅ 正确做法：** 有条件导入，有降级方案

---

#### 3. qiniu（storage_manager.py, auto_cleanup.py）

```python
try:
    import qiniu
    from qiniu import Auth, put_file_v2, BucketManager
except ImportError:
    qiniu = None  # 或 sys.exit(1)
```

**✅ 正确做法：** 检查 SDK 是否存在

**但问题：**
- `storage_manager.py` 返回错误消息
- `auto_cleanup.py` 直接退出程序

**建议统一处理：**
```python
if qiniu is None:
    return {"error": "七牛云 SDK 未安装", "download_url": None}
```

---

#### 4. EmbeddingAPI（agent_file_cloud.py）

```python
try:
    from embedding_api import EmbeddingAPI
    self.embedding_api = EmbeddingAPI(...)
except Exception as e:
    print(f"⚠️ Embedding API 加载失败：{e}")
    print("   将使用关键词搜索（降级模式）")
```

**✅ 正确做法：** 有降级方案

---

## 🚨 发现的问题

### 1. numpy 无降级处理 🔴

**问题：** `embedding_api.py` 的 `cosine_similarity()` 直接使用 numpy

**影响：**
- numpy 未安装 → 语义搜索完全失效
- 无错误提示，用户不知道发生了什么

**修复：**
```python
# embedding_api.py 开头
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

def cosine_similarity(self, vec1, vec2):
    """计算余弦相似度（支持无 numpy 降级）"""
    if not HAS_NUMPY:
        # 纯 Python 实现
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    # numpy 实现（更快）
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    # ...
```

---

### 2. 缺少 requirements.txt ✅ 已创建

**问题：** 之前没有 requirements.txt 文件

**已修复：**
```txt
# 核心依赖
numpy>=1.24.0
qiniu>=7.17.0
networkx>=3.0

# 可选依赖
dashscope>=1.0.0
faiss-cpu>=1.7.0
openai>=1.0.0
```

---

### 3. SKILL.md 依赖说明混乱 🟡

**问题：**
- 多处提到 `pip3 install`
- 依赖列表不完整
- 未区分必需/可选

**建议：**
```markdown
## 🔧 依赖安装

### 必需依赖
pip3 install numpy qiniu

### 可选依赖
pip3 install networkx  # 图谱分析
pip3 install faiss-cpu  # 大数据量搜索加速
```

---

### 4. 虚拟环境未使用 🟡

**问题：**
- 存在 `venv/` 目录
- 但实际使用全局 Python
- venv 中无包

**建议：**
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

### 5. 依赖版本未锁定 🟢

**问题：** requirements.txt 使用 `>=` 而非 `==`

**影响：** 不同环境可能安装不同版本

**建议：**
```txt
# 开发环境（严格版本）
numpy==1.26.4
qiniu==7.17.0

# 生产环境（允许小版本更新）
numpy>=1.24.0,<2.0.0
```

---

## 📊 依赖健康度

| 维度 | 得分 | 说明 |
|------|------|------|
| 必需依赖管理 | ⭐⭐ | 缺少 numpy 降级 |
| 可选依赖处理 | ⭐⭐⭐⭐ | 大部分有 try-except |
| 文档完整性 | ⭐⭐ | SKILL.md 混乱 |
| 版本控制 | ⭐⭐ | 未锁定版本 |
| 虚拟环境 | ⭐⭐ | 存在但未使用 |
| **总体** | **⭐⭐** | 基础可用，需改进 |

---

## 🎯 修复建议

### 立即修复

1. **添加 numpy 降级方案** - 防止语义搜索崩溃
2. **更新 SKILL.md** - 明确必需/可选依赖
3. **添加安装检查** - 启动时验证依赖

### 中期改进

4. **使用虚拟环境** - 隔离依赖
5. **锁定依赖版本** - 使用 `requirements.lock`
6. **添加依赖测试** - CI 中验证

---

## 📝 推荐的 requirements.txt

```txt
# Agent File Cloud - 核心依赖

# 必需
numpy>=1.24.0,<2.0.0      # 向量计算
qiniu>=7.17.0,<8.0.0      # 七牛云上传

# 可选（功能增强）
networkx>=3.0             # 图谱分析
faiss-cpu>=1.7.0          # 大规模向量搜索

# 开发
pytest>=7.0.0             # 测试
```

---

## 🧪 依赖检查脚本

```python
#!/usr/bin/env python3
"""检查依赖是否完整"""

import sys

def check_dependencies():
    required = {'numpy': '向量计算', 'qiniu': '七牛云上传'}
    optional = {'networkx': '图谱分析', 'faiss': '向量索引'}
    
    missing_required = []
    missing_optional = []
    
    for pkg, desc in required.items():
        try:
            __import__(pkg)
        except ImportError:
            missing_required.append(f"{pkg} ({desc})")
    
    for pkg, desc in optional.items():
        try:
            __import__(pkg)
        except ImportError:
            missing_optional.append(f"{pkg} ({desc})")
    
    if missing_required:
        print("❌ 缺少必需依赖:")
        for m in missing_required:
            print(f"   - {m}")
        return False
    
    if missing_optional:
        print("⚠️  缺少可选依赖:")
        for m in missing_optional:
            print(f"   - {m}")
    
    print("✅ 所有必需依赖已安装")
    return True

if __name__ == "__main__":
    sys.exit(0 if check_dependencies() else 1)
```

---

**审查完成！** 🦞
