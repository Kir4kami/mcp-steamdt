# 发布到 PyPI 指南

## 前置准备

1. **注册 PyPI 账号**
   - 访问 https://pypi.org/account/register/
   - 注册账号并验证邮箱

2. **安装构建工具**
   ```bash
   pip install build twine
   ```

3. **配置 API Token（推荐）**
   - 登录 PyPI，进入 Account settings → API tokens
   - 创建新的 API token，保存好 token 值

## 发布步骤

### 1. 更新版本号

编辑 `pyproject.toml`，更新 `version` 字段：
```toml
version = "0.1.0"  # 改为新版本号，如 0.1.1
```

### 2. 构建包

```bash
# 清理旧的构建文件
rm -rf dist/ build/ *.egg-info

# 构建包
python -m build
```

### 3. 检查构建结果

```bash
# 检查构建的文件
ls dist/

# 应该看到：
# - steamdt-mcp-0.1.0.tar.gz
# - steamdt_mcp-0.1.0-py3-none-any.whl
```

### 4. 上传到 PyPI

**使用 API Token（推荐）：**
```bash
# 设置环境变量（Windows PowerShell）
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "你的API_TOKEN"

# 上传
python -m twine upload dist/*
```

**或使用用户名密码：**
```bash
python -m twine upload dist/*
# 输入用户名和密码
```

### 5. 验证发布

发布成功后，可以通过以下方式验证：

```bash
# 使用 uvx 测试（会自动下载最新版本）
uvx steamdt-mcp --help

# 或使用 pip 安装测试
pip install steamdt-mcp
```

## 发布后

发布成功后，用户就可以直接使用：

```bash
uvx steamdt-mcp
```

无需克隆仓库！

## 注意事项

1. **版本号规范**：遵循 [语义化版本](https://semver.org/)
   - MAJOR.MINOR.PATCH（如 1.0.0）
   - 修复 bug：0.1.0 → 0.1.1
   - 新功能：0.1.0 → 0.2.0
   - 重大变更：0.1.0 → 1.0.0

2. **测试发布**：可以先发布到 [TestPyPI](https://test.pypi.org/) 测试
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

3. **更新 README**：发布后记得更新 README 中的版本号（如果有提到）

## 自动化发布（可选）

可以使用 GitHub Actions 自动化发布流程，参考其他开源项目的 workflow 配置。

