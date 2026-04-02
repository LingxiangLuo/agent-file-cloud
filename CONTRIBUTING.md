# 贡献指南

感谢你对 Agent File Cloud 项目的关注！本文档将指导你如何为项目做出贡献。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码风格](#代码风格)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)

---

## 行为准则

- 尊重他人，保持友好的交流
- 对事不对人，专注于技术讨论
- 欢迎不同观点，保持开放心态

---

## 如何贡献

你可以通过以下方式贡献：

1. **报告 Bug**: 在 Issues 中详细描述问题
2. **功能建议**: 在 Issues 中提出新功能想法
3. **代码贡献**: 提交 PR 修复 Bug 或实现功能
4. **文档改进**: 修正文档错误或补充说明

---

## 开发环境设置

### 1. Fork 项目

```bash
# 在 GitHub 上点击 Fork 按钮
```

### 2. 克隆到本地

```bash
git clone https://github.com/YOUR_USERNAME/agent-file-cloud.git
cd agent-file-cloud
```

### 3. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制配置模板
cp config/config.example.json config/config.json

# 编辑配置文件，填入你的 API 密钥
```

### 5. 运行测试

```bash
python3 -m pytest tests/
```

---

## 代码风格

### Python 代码规范

1. **类型注解**: 所有公共函数必须添加类型注解

```python
def add_file(filepath: str, tags: Optional[List[str]] = None) -> Dict:
    """添加文件到数据库"""
```

2. **文档字符串**: 所有公共函数必须有文档字符串

```python
def search(query: str, k: int = 10) -> List[Dict]:
    """
    搜索文件

    Args:
        query: 搜索查询
        k: 返回数量

    Returns:
        搜索结果列表
    """
```

3. **错误处理**: 使用适当的异常处理

```python
try:
    result = api.create_embedding(text)
except Exception as e:
    return {"error": f"API 调用失败：{e}"}
```

4. **命名规范**:
   - 类名：大驼峰 (PascalCase) - `StorageManager`
   - 函数/变量：小写 + 下划线 (snake_case) - `get_file_category`
   - 常量：全大写 + 下划线 - `MAX_RETRIES`

### 代码格式化

使用以下工具检查代码质量：

```bash
# 检查代码风格
flake8 .

# 检查类型注解
mypy .

# 格式化代码
black .
```

---

## 提交规范

### Commit Message 格式

我们遵循约定式提交规范：

```
<type>: <subject>

[optional body]

[optional footer]
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码风格（格式化、分号等）
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具/配置

### 示例

```bash
# 新功能
git commit -m "feat: 添加批量上传功能"

# Bug 修复
git commit -m "fix: 修复搜索结果为空时的异常"

# 文档更新
git commit -m "docs: 更新 API 使用示例"

# 代码风格
git commit -m "style: 添加类型注解和文档字符串"

# 关联 Issue
git commit -m "fix: 修复路径遍历漏洞 (fixes #12)"
```

---

## Pull Request 流程

### 1. 创建分支

```bash
# 从 main 创建新分支
git checkout -b feature/your-feature-name

# 或者修复分支
git checkout -b fix/issue-12
```

### 2. 开发并提交

```bash
# 开发完成后提交
git add .
git commit -m "feat: 实现你的功能"
```

### 3. 推送分支

```bash
git push origin feature/your-feature-name
```

### 4. 创建 PR

1. 在 GitHub 上进入你的 Fork
2. 点击 "Compare & pull request"
3. 填写 PR 描述：
   - 做了什么改动
   - 为什么需要这些改动
   - 如何测试这些改动

### 5. Code Review

- 等待维护者审查
- 根据反馈修改代码
- 审查通过后合并

---

## 分支命名

- 功能开发：`feature/<功能名>` - `feature/batch-upload`
- Bug 修复：`fix/<问题描述>` - `fix/search-encoding`
- 文档更新：`docs/<文档名>` - `docs/api-reference`
- 重构：`refactor/<模块名>` - `refactor/data-manager`

---

## 测试要求

提交 PR 前确保：

- [ ] 现有测试通过
- [ ] 新增功能有对应测试
- [ ] 代码通过风格检查
- [ ] 文档已更新

运行测试：

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行单个测试
python3 -m pytest tests/test_data_manager.py -v
```

---

## 问题反馈

遇到问题？请通过以下方式反馈：

1. 查看 [现有 Issues](https://github.com/LingxiangLuo/agent-file-cloud/issues) 是否已有相同问题
2. 创建新 Issue，提供：
   - 问题描述
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息（Python 版本、OS 等）

---

## 许可证

提交代码即表示你同意将代码以 MIT 许可证发布。

---

## 感谢贡献者

感谢所有为这个项目做出贡献的人！
