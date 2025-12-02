# 项目结构说明

```
mcp-steamdt/
├── steamdt_mcp/          # 核心 MCP 服务器代码
│   ├── __init__.py       # 包初始化
│   └── server.py         # MCP 服务器主文件（包含所有工具）
├── scripts/              # 辅助脚本
│   └── cache_base_info.py # 手动缓存基础信息脚本（可选）
├── README.md             # 项目说明和快速开始
├── USAGE.md              # 详细使用指南
├── PUBLISH.md            # PyPI 发布指南（可选）
├── pyproject.toml        # Python 项目配置（支持 pip install git+）
├── requirements.txt      # Python 依赖
├── .gitignore            # Git 忽略规则
└── claude_desktop_config.example.json  # Claude Desktop 配置示例
```

## 文件说明

### 核心代码
- `steamdt_mcp/server.py` - MCP 服务器，包含所有工具函数
- `steamdt_mcp/__init__.py` - 包初始化文件

### 文档
- `README.md` - 项目概览和快速开始
- `USAGE.md` - 详细使用指南和常见问题
- `PUBLISH.md` - 如何发布到 PyPI（可选）

### 配置
- `pyproject.toml` - Python 项目元数据，支持 `pip install git+...`
- `requirements.txt` - Python 依赖列表
- `.gitignore` - Git 忽略规则
- `claude_desktop_config.example.json` - MCP 客户端配置示例

### 脚本
- `scripts/cache_base_info.py` - 手动缓存基础信息脚本（可选）

## 不包含的文件

以下文件不应提交到仓库（已在 .gitignore 中）：
- `steam_items_base.json` - 用户本地缓存文件（太大，用户自己生成）
- `test_*.py` - 测试脚本（开发用）
- `.venv/` - 虚拟环境
- `__pycache__/` - Python 缓存
- `.env` - 环境变量文件（包含 API 密钥）

