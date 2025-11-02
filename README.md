# ArxivDigest-Reimagined

[English](README.md) | [中文（机翻）](README-CN.md)

**ArxivDigest-Reimagined** is an intelligent arXiv paper filtering and digest generation system powered by LLMs. It uses a three-stage progressive filtering pipeline to help researchers quickly identify papers relevant to their interests from the daily arXiv feed. (Inspired by [ArxivDigest](https://github.com/AutoLLM/ArxivDigest).)

![](assets/readme-image.png)

## 📚 Table of Contents

[toc]

## 🌟 Features

-   **Three-Stage Progressive Filtering**: Efficiently narrows down papers through increasingly detailed analysis
    -   **Stage 1**: Quick screening based on title and categories
    -   **Stage 2**: Refined filtering with authors and abstracts
    -   **Stage 3**: Deep analysis using full paper content from arXiv HTML
-   **Smart Abstract Highlighting**: Automatically highlights key points in abstracts using LLM
-   **Rich Paper Analysis**: Extracts novelty, impact, quality scores, and custom fields

## 📦 Requirements

**Backend**:

-   Python 3.12+ (lower versions not tested)
-   `uv` (recommended for dependency management)
-   API key for LLM service (tested with DeepSeek-Chat)

**Frontend**:

-   Node.js 20.19+ or 22.12+ (lower versions not tested)
-   npm or pnpm

## 🚀 Usage

### Option 1: GitHub Actions (Automated Daily Digest)

1. **Fork this repository**

2. **Set up secrets and variables**:

    - Go to your repo's Settings → Secrets and variables → Actions
    - **Add a secret** named `API_KEY` with your LLM API key (e.g., DeepSeek API key)
    - **Add a variable** named `CONFIG_YAML`:
        - Click on the "Variables" tab
        - Click "New repository variable"
        - Name: `CONFIG_YAML`
        - Value: Copy the entire content of [`backend/config_example.yaml`](backend/config_example.yaml) and customize it with your research interests (see [Configuration](#-configuration) for details)
        - Save the variable

3. **Configure the workflow** (optional):

    - Edit `.github/workflows/daily-digest.yml` to change the schedule
    - Default: runs at 00:00 AM UTC (08:00 AM Beijing Time) daily

4. **Enable GitHub Pages**:

    - Go to Settings → Pages
    - Source: GitHub Actions
    - The workflow will automatically deploy to GitHub Pages after running

5. **Manual trigger** (optional):
    - Go to Actions → "Generate Daily Digest" → Run workflow
    - View the deployed site at `https://<username>.github.io/<repo-name>/`

> **Note**: When you want to update your filtering criteria, just edit the `CONFIG_YAML` variable in GitHub settings. No need to commit any code changes!

### Option 2: Run Locally (Manual)

**Backend Setup**:

```bash
cd backend

# Install uv if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Copy the example config and customize it
cp config_example.yaml config.yaml
# Edit config.yaml to set your research interests and filtering criteria

# Create .env file with your API key
echo "API_KEY=your-api-key-here" > .env

# Run the digest generation
uv run main.py
```

This will:

-   Fetch papers from arXiv based on `config.yaml` settings
-   Run the three-stage filtering pipeline
-   Generate `frontend/public/digest.json`

**Frontend Setup**:

```bash
cd frontend

# Install dependencies
npm install

# Development mode (with hot reload)
npm run dev

# Or build for production
npm run build
npm run preview
```

Visit `http://localhost:5173` (dev) or `http://localhost:4173` (preview) to view the digest.

## ⚙️ Configuration

The configuration file controls all aspects of paper filtering and analysis.

**For local development**: Copy `backend/config_example.yaml` to `backend/config.yaml` and customize it.

**For GitHub Actions**: Store the entire config content in the `CONFIG_YAML` repository variable (see [Usage](#-usage)).

### Configuration Options

```yaml
arxiv:
    field: "cs" # arXiv field (cs, math, physics, etc.)
    categories:
        - "Computer Vision and Pattern Recognition"
        - "Artificial Intelligence"
    max_results: 0 # 0 = no limit

llm:
    model: "deepseek-chat" # LLM model name
    base_url: "https://api.deepseek.com"
    max_concurrent: 10
    timeout: 60

user_prompt: |
    Your research interests and filtering criteria.
    Be specific about topics, methods, or applications you care about.
    You can also specify the language for LLM responses.

stage1:
    threshold: 0.5 # Lower = more inclusive
    temperature: 0.0

stage2:
    threshold: 0.7
    temperature: 0.1

stage3:
    threshold: 0.8
    temperature: 0.3
    max_text_chars: 40000 # Max characters to extract from paper HTML
    custom_fields:
        - name: "key_innovations"
          description: "List the core innovations and contributions"
        - name: "technical_approach"
          description: "Outline the technical methods used"
        - name: "limitations"
          description: "Identify limitations or areas for improvement"
        - name: "potential_impact"
          description: "Assess the potential impact on the field"

highlight:
    temperature: 0.0 # Temperature for abstract highlighting

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

**Configuration Tips:**

-   Check `backend/config_example.yaml` for the complete example with detailed comments.
-   **Be specific with your `user_prompt`**: Overly broad filtering criteria may allow too many papers to reach Stage 3, consuming significant tokens. If you need broad filtering, consider:
    -   Adjusting `threshold` values (higher = more selective)
    -   Setting a lower `max_results` to limit the number of papers processed
    -   Making your prompt more specific about what you're looking for
-   **Customize `custom_fields` for your needs**: You can ask LLM to analyze ANY aspect of papers, be creative! Examples:

    ```yaml
    - name: "rl_algorithm"
      description: "If the paper uses reinforcement learning, specify the algorithms used"
    - name: "code_availability"
      description: "Is the code open-sourced? Provide the link if available"
    - name: "related_work"
      description: "How does this paper relate to my ongoing project on [specific topic]?"
    - name: "computational_requirements"
      description: "Summarize the computational requirements mentioned in the paper"
    ```

## 🔧 Development

**Backend**:

```bash
cd backend
uv run ruff check .  # Lint
uv run ruff format .  # Format
```

**Frontend**:

```bash
cd frontend
npm run lint    # Lint & fix
npm run format  # Format with Prettier
```

## 📝 License

[GPLv3 License](LICENSE)
