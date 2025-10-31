# ArxivDigest-Reimagined

Three-stage progressive filtering system for arXiv papers with LLM-powered analysis.

## Architecture

### Backend (Python)

-   **Fetcher**: Scrapes arXiv papers and HTML content
-   **Filter Pipeline**: Three-stage progressive filtering with DeepSeek LLM
    -   Stage 1: Quick screening (Title + Categories)
    -   Stage 2: Refined screening (+ Authors + Abstract)
    -   Stage 3: Deep analysis (+ Full Paper Content)
-   **Cache**: Persistent caching with configuration-aware invalidation
-   **Exporter**: Outputs comprehensive JSON digest

### Frontend (Vue 3 + TypeScript)

-   **Modern Stack**: Vue 3, TypeScript, Tailwind CSS, Vite
-   **Type Safety**: Zod schemas for runtime validation
-   **Components**: Modular UI with HeadlessUI
-   **Features**: Stage filtering, conversation viewer, responsive design

## Quick Start

### Backend

```bash
cd backend
uv run main.py
```

Output: `frontend/public/digest.json`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

See `frontend/SETUP.md` for detailed setup instructions.

## Configuration

Edit `backend/config.yaml` to customize:

-   arXiv categories and result limits
-   LLM model and parameters
-   Stage thresholds and custom fields
-   Cache settings

## Development

-   Backend uses `uv` for dependency management
-   Frontend uses `nvm` for Node.js version management
-   Tailwind CSS for styling
-   ESLint + Prettier for code quality
