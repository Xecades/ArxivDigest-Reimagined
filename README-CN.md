# ArxivDigest-Reimagined

[English](README.md) | [中文（机翻）](README-CN.md)

**ArxivDigest-Reimagined** 是一个由大语言模型驱动的智能 arXiv 论文筛选和摘要生成系统。它使用三阶段渐进式筛选流程，帮助研究人员从每日 arXiv 论文中快速识别出与自己研究兴趣相关的论文。（灵感来自 [ArxivDigest](https://github.com/AutoLLM/ArxivDigest)。）

> 在线示例：https://arxiv.xecades.xyz/ （注意：我的研究兴趣比较具体，所以每天可能没有多少第三阶段的论文。如果想要完整体验，建议用你自己的兴趣配置试试看！）

![](assets/readme-image.png)

## 🌟 功能特性

-   **三阶段渐进式筛选**：通过逐步深入的分析高效筛选论文
    -   **第一阶段**：基于标题和类别的快速筛选
    -   **第二阶段**：结合作者和摘要的精细筛选
    -   **第三阶段**：使用 arXiv HTML 完整论文内容的深度分析
-   **智能摘要高亮**：使用 LLM 自动高亮摘要中的关键点
-   **丰富的论文分析**：提取新颖性、影响力、质量评分和自定义分析字段

## 📦 环境要求

**后端**：

-   Python 3.12+（更低版本未测试）
-   `uv`（推荐用于依赖管理）
-   LLM 服务的 API 密钥（已测试 DeepSeek-Chat）

**前端**：

-   Node.js 20.19+ 或 22.12+（更低版本未测试）
-   npm 或 pnpm

## 🚀 使用方法

### 方案一：GitHub Actions（自动每日摘要）

1. **Fork 本仓库**

2. **设置密钥和变量**：

    - 进入仓库的 Settings → Secrets and variables → Actions
    - **添加密钥** `API_KEY`，值为你的 LLM API 密钥（如 DeepSeek API 密钥）
    - **添加变量** `CONFIG_YAML`：
        - 点击 "Variables" 标签
        - 点击 "New repository variable"
        - Name: `CONFIG_YAML`
        - Value: 复制 [`backend/config_example.yaml`](backend/config_example.yaml) 的全部内容，并根据你的研究兴趣进行自定义（详见[配置说明](#-配置说明)）
        - 保存变量
    - **添加变量** `BASE_URL`（可选）：
        - 仅在部署到自定义域名或非根路径时需要
        - 示例：`/my-digest/` 或 `/`
        - 如果不设置，将自动使用 `/<仓库名>/`（例如 `/ArxivDigest-Reimagined/`）

3. **配置工作流**（可选）：

    - 编辑 `.github/workflows/daily-digest.yml` 修改运行时间
    - 默认：每天 UTC 时间 00:00（北京时间 08:00）运行

4. **启用 GitHub Pages**：

    - 进入 Settings → Pages
    - Source 选择：GitHub Actions
    - 工作流运行后会自动部署到 GitHub Pages

5. **手动触发**（可选）：
    - 进入 Actions → "Generate Daily Digest" → Run workflow
    - 访问部署的网站：`https://<用户名>.github.io/<仓库名>/`

> **提示**：当你想更新筛选条件时，只需编辑 GitHub 设置中的 `CONFIG_YAML` 变量，无需提交代码更改！

### 方案二：本地运行（手动）

**后端设置**：

```bash
cd backend

# 安装 uv（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync

# 复制示例配置并自定义
cp config_example.yaml config.yaml
# 编辑 config.yaml 设置你的研究兴趣和筛选条件

# 创建 .env 文件并添加 API 密钥
echo "API_KEY=你的API密钥" > .env

# 运行摘要生成
uv run main.py
```

这将会：

-   根据 `config.yaml` 的设置从 arXiv 获取论文
-   运行三阶段筛选流程
-   生成 `frontend/public/digest.json`

**前端设置**：

```bash
cd frontend

# 安装依赖
npm install

# 开发模式（支持热重载）
npm run dev

# 或构建生产版本
npm run build
npm run preview
```

访问 `http://localhost:5173`（开发模式）或 `http://localhost:4173`（预览模式）查看摘要。

## ⚙️ 配置说明

配置文件控制论文筛选和分析的所有方面。

**本地开发**：复制 `backend/config_example.yaml` 为 `backend/config.yaml` 并自定义。

**GitHub Actions**：将完整配置内容存储在 `CONFIG_YAML` 仓库变量中（参见[使用方法](#-使用方法)）。

### 配置选项

```yaml
arxiv:
    field: "cs" # arXiv 领域（cs, math, physics 等）
    # 也可以指定多个领域：
    # field:
    #   - "cs"
    #   - "math"
    #   - "stat"
    categories:
        - "Computer Vision and Pattern Recognition"
        - "Artificial Intelligence"
    max_results: 0 # 0 = 不限制数量

llm:
    model: "deepseek-chat" # LLM 模型名称
    base_url: "https://api.deepseek.com"
    max_concurrent: 10
    timeout: 60

user_prompt: |
    你的研究兴趣和筛选条件。
    请具体说明你关心的主题、方法或应用。
    你也可以指定 LLM 响应的语言。

stage1:
    threshold: 0.5 # 越低越包容
    temperature: 0.0

stage2:
    threshold: 0.7
    temperature: 0.1

stage3:
    threshold: 0.8
    temperature: 0.3
    max_text_chars: 40000 # 从论文 HTML 提取的最大字符数
    custom_fields:
        - name: "key_innovations"
          description: "列出核心创新点和贡献"
        - name: "technical_approach"
          description: "概述使用的技术方法"
        - name: "limitations"
          description: "指出局限性或需要改进的地方"
        - name: "potential_impact"
          description: "评估对该领域的潜在影响"

highlight:
    temperature: 0.0 # 摘要高亮的温度参数

cache:
    dir: ".cache"
    size_limit_mb: 1024
    expire_days: 30

crawler:
    max_concurrent: 5
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
```

**配置技巧**：

-   查看 `backend/config_example.yaml` 获取带有详细注释的完整示例。
-   **明确你的 `user_prompt`**：过于宽泛的筛选条件可能会让太多论文进入第三阶段，消耗大量 token。如果你确实需要宽泛的筛选，可以考虑：
    -   调整 `threshold` 值（越高越严格）
    -   设置较低的 `max_results` 限制处理的论文数量
    -   让你的 prompt 更具体明确
-   **根据需求自定义 `custom_fields`**：你可以让 LLM 分析论文的任何方面，发挥创意！示例：

    ```yaml
    - name: "rl_algorithm"
      description: "如果论文使用了强化学习，请说明使用的算法"
    - name: "code_availability"
      description: "代码是否开源？如果有请提供链接"
    - name: "related_work"
      description: "这篇论文如何与我正在进行的[具体主题]项目相关？"
    - name: "computational_requirements"
      description: "总结论文中提到的计算资源需求"
    ```

## 🔧 开发

**后端**：

```bash
cd backend
uv run ruff check .  # 代码检查
uv run ruff format .  # 代码格式化
```

**前端**：

```bash
cd frontend
npm run lint    # 代码检查和修复
npm run format  # 使用 Prettier 格式化
```

## 📝 许可证

[GPLv3 License](LICENSE)
