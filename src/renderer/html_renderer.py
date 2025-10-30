"""HTML renderer with interactive stage filtering support."""

import json
from datetime import datetime

from loguru import logger


class HTMLRenderer:
    """
    Renders an interactive HTML digest with stage-based filtering.

    Allows users to view papers from different filtering stages
    with a clean, responsive interface and stage selector.
    """

    def __init__(self):
        """Initialize the HTML renderer."""
        logger.debug("HTMLRenderer initialized")

    def render(
        self,
        pipeline_results: dict,
        output_path: str = "digest.html",
        title: str = "ArXiv Digest - Reimagined",
    ) -> None:
        """
        Render pipeline results to interactive HTML file.

        Args:
            pipeline_results: Dictionary with all stage results from FilterPipeline
            output_path: Output file path
            title: Page title
        """
        # Extract all stage results
        stage1_results = pipeline_results["stage1_results"]
        stage2_results = pipeline_results["stage2_results"]
        stage3_results = pipeline_results["stage3_results"]

        # Count papers at each stage
        stage1_total = len(stage1_results)
        stage1_passed = len([r for _, r in stage1_results if r.pass_filter])
        stage2_passed = len([r for _, r in stage2_results if r.pass_filter])
        stage3_passed = len([r for _, r in stage3_results if r and r.pass_filter])

        logger.info(
            f"Rendering HTML: {stage1_total} total, "
            f"{stage1_passed} stage1, {stage2_passed} stage2, {stage3_passed} stage3"
        )

        # Prepare data for JavaScript
        papers_data = self._prepare_papers_data(pipeline_results)

        # Generate HTML
        html_content = self._generate_html(
            papers_data=papers_data,
            title=title,
            stage1_total=stage1_total,
            stage1_passed=stage1_passed,
            stage2_passed=stage2_passed,
            stage3_passed=stage3_passed,
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.success(f"HTML digest saved to: {output_path}")

    def _prepare_papers_data(self, pipeline_results: dict) -> list[dict]:
        """
        Prepare papers data for JavaScript rendering.

        Args:
            pipeline_results: Pipeline results dictionary

        Returns:
            List of paper data dictionaries
        """
        papers_map = {}

        # Stage 1 results (all papers)
        for paper, result in pipeline_results["stage1_results"]:
            paper_id = paper["id"]
            papers_map[paper_id] = {
                "arxiv_id": paper_id,
                "title": paper["title"],
                "authors": paper["authors"],
                "categories": paper["categories"],
                "abstract": paper.get("abstract", ""),
                "pdf_url": paper.get("pdf_url", ""),
                "abs_url": paper.get("abs_url", ""),
                "published": paper.get("published", ""),
                "stage1": {
                    "pass": result.pass_filter,
                    "score": result.score,
                    "reasoning": getattr(result, "reasoning", ""),
                },
                "stage2": None,
                "stage3": None,
                "max_stage": 1 if result.pass_filter else 0,
            }

        # Stage 2 results
        for paper, result in pipeline_results["stage2_results"]:
            paper_id = paper["id"]
            if paper_id in papers_map:
                papers_map[paper_id]["stage2"] = {
                    "pass": result.pass_filter,
                    "score": result.score,
                    "reasoning": getattr(result, "reasoning", ""),
                    "category": getattr(result, "category", ""),
                }
                if result.pass_filter:
                    papers_map[paper_id]["max_stage"] = 2

        # Stage 3 results
        for paper, result in pipeline_results["stage3_results"]:
            if result is None:
                continue
            paper_id = paper["id"]
            if paper_id in papers_map:
                stage3_data = {
                    "pass": result.pass_filter,
                    "score": result.score,
                    "novelty_score": result.novelty_score,
                    "impact_score": result.impact_score,
                    "quality_score": result.quality_score,
                    "reasoning": result.reasoning,
                }
                # Add custom fields
                if hasattr(result, "custom_fields") and result.custom_fields:
                    stage3_data["custom_fields"] = result.custom_fields

                papers_map[paper_id]["stage3"] = stage3_data
                if result.pass_filter:
                    papers_map[paper_id]["max_stage"] = 3

        # Convert to list and sort by max_stage (descending) and score
        papers_list = list(papers_map.values())
        papers_list.sort(
            key=lambda p: (
                p["max_stage"],
                p["stage3"]["score"]
                if p["stage3"]
                else p["stage2"]["score"]
                if p["stage2"]
                else p["stage1"]["score"],
            ),
            reverse=True,
        )

        return papers_list

    def _generate_html(
        self,
        papers_data: list[dict],
        title: str,
        stage1_total: int,
        stage1_passed: int,
        stage2_passed: int,
        stage3_passed: int,
    ) -> str:
        """Generate complete HTML document."""
        papers_json = json.dumps(papers_data, ensure_ascii=False, indent=2)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine default stage (highest non-empty stage)
        default_stage = "all"
        if stage3_passed > 0:
            default_stage = "3"
        elif stage2_passed > 0:
            default_stage = "2"
        elif stage1_passed > 0:
            default_stage = "1"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html {{
            min-height: 100vh;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) fixed;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        header .timestamp {{
            opacity: 0.9;
            font-size: 0.9em;
        }}
        
        .controls {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .stage-selector {{
            display: flex;
            gap: 10px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: thin;
            scrollbar-color: #667eea #e9ecef;
        }}
        
        .stage-selector::-webkit-scrollbar {{
            height: 6px;
        }}
        
        .stage-selector::-webkit-scrollbar-track {{
            background: #e9ecef;
            border-radius: 3px;
        }}
        
        .stage-selector::-webkit-scrollbar-thumb {{
            background: #667eea;
            border-radius: 3px;
        }}
        
        .stage-btn {{
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            font-size: 0.9em;
            white-space: nowrap;
            flex-shrink: 0;
        }}
        
        .stage-btn:hover {{
            background: #667eea;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        
        .stage-btn:active {{
            transform: translateY(0);
        }}
        
        .stage-btn.active {{
            background: #667eea;
            color: white;
        }}
        
        .stats {{
            display: flex;
            gap: 20px;
            font-size: 0.9em;
            color: #666;
        }}
        
        .stat {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .stat-value {{
            font-weight: bold;
            color: #667eea;
        }}
        
        .papers-container {{
            padding: 30px;
        }}
        
        .paper-card {{
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
            display: none;
        }}
        
        .paper-card.visible {{
            display: block;
        }}
        
        .paper-card:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }}
        
        .paper-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
            gap: 20px;
        }}
        
        .paper-title {{
            font-size: 1.4em;
            font-weight: 600;
            color: #2c3e50;
            flex: 1;
        }}
        
        .paper-title a {{
            color: #2c3e50;
            text-decoration: none;
            transition: color 0.3s ease;
        }}
        
        .paper-title a:hover {{
            color: #667eea;
        }}
        
        .stage-badges {{
            display: flex;
            gap: 8px;
            flex-shrink: 0;
        }}
        
        .stage-badge {{
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        
        .stage-badge.stage-1 {{
            background: #d4edda;
            color: #155724;
        }}
        
        .stage-badge.stage-2 {{
            background: #cce5ff;
            color: #004085;
        }}
        
        .stage-badge.stage-3 {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .paper-meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }}
        
        .authors {{
            margin-bottom: 8px;
        }}
        
        .categories {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        
        .category-tag {{
            background: #e9ecef;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
        }}
        
        .abstract-toggle {{
            background: none;
            border: none;
            color: #667eea;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9em;
            padding: 8px 0;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: color 0.3s ease;
            -webkit-tap-highlight-color: transparent;
            user-select: none;
        }}
        
        .abstract-toggle:hover {{
            color: #764ba2;
        }}
        
        .abstract-toggle:active {{
            opacity: 0.7;
        }}
        
        .abstract-toggle-icon {{
            transition: transform 0.3s ease;
        }}
        
        .abstract-toggle.expanded .abstract-toggle-icon {{
            transform: rotate(90deg);
        }}
        
        .paper-abstract {{
            color: #555;
            margin-bottom: 15px;
            line-height: 1.7;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        
        .paper-abstract.expanded {{
            max-height: 1000px;
        }}
        
        .scores {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }}
        
        .score-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .score-label {{
            font-weight: 600;
            color: #666;
            font-size: 0.9em;
        }}
        
        .score-bar {{
            width: 100px;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .score-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }}
        
        .score-value {{
            font-weight: bold;
            color: #667eea;
            font-size: 0.9em;
        }}
        
        .reasoning {{
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #667eea;
            border-radius: 4px;
            margin-bottom: 15px;
        }}
        
        .reasoning-title {{
            font-weight: 600;
            color: #667eea;
            margin-bottom: 8px;
        }}
        
        .reasoning-text {{
            color: #555;
            line-height: 1.7;
        }}
        
        .custom-fields {{
            margin-top: 15px;
        }}
        
        .custom-field {{
            margin-bottom: 12px;
        }}
        
        .custom-field-title {{
            font-weight: 600;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .custom-field-content {{
            color: #555;
            line-height: 1.7;
        }}
        
        .no-papers {{
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }}
        
        .no-papers-icon {{
            font-size: 4em;
            margin-bottom: 20px;
        }}
        
        footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            header {{
                padding: 20px 15px;
            }}
            
            header h1 {{
                font-size: 1.8em;
            }}
            
            .container {{
                border-radius: 8px;
            }}
            
            .controls {{
                flex-direction: column;
                align-items: stretch;
                padding: 15px;
                gap: 10px;
            }}
            
            .stage-selector {{
                justify-content: flex-start;
                gap: 8px;
                flex-wrap: nowrap;
                padding-bottom: 5px;
            }}
            
            .stage-btn {{
                padding: 8px 15px;
                font-size: 0.85em;
            }}
            
            .stats {{
                justify-content: center;
                font-size: 0.85em;
            }}
            
            .papers-container {{
                padding: 15px;
            }}
            
            .paper-card {{
                padding: 15px;
                margin-bottom: 15px;
            }}
            
            .paper-header {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .paper-title {{
                font-size: 1.2em;
            }}
            
            .stage-badges {{
                justify-content: flex-start;
            }}
            
            .paper-meta {{
                font-size: 0.85em;
            }}
            
            .categories {{
                gap: 5px;
            }}
            
            .category-tag {{
                font-size: 0.8em;
                padding: 2px 8px;
            }}
            
            .abstract-toggle {{
                font-size: 0.85em;
            }}
            
            .scores {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .score-item {{
                width: 100%;
            }}
            
            .score-bar {{
                flex: 1;
                min-width: 100px;
            }}
            
            .reasoning {{
                padding: 12px;
                font-size: 0.9em;
            }}
            
            .custom-field {{
                font-size: 0.9em;
            }}
            
            footer {{
                padding: 15px;
                font-size: 0.85em;
            }}
        }}
        
        @media (max-width: 480px) {{
            body {{
                padding: 5px;
            }}
            
            header {{
                padding: 15px 10px;
            }}
            
            header h1 {{
                font-size: 1.5em;
            }}
            
            .timestamp {{
                font-size: 0.8em;
            }}
            
            .controls {{
                padding: 10px;
            }}
            
            .stage-selector {{
                gap: 6px;
            }}
            
            .stage-btn {{
                padding: 6px 12px;
                font-size: 0.8em;
            }}
            
            .papers-container {{
                padding: 10px;
            }}
            
            .paper-card {{
                padding: 12px;
            }}
            
            .paper-title {{
                font-size: 1.1em;
            }}
            
            .stage-badge {{
                font-size: 0.75em;
                padding: 4px 10px;
            }}
        }}
        
        /* Touch device optimizations */
        @media (hover: none) and (pointer: coarse) {{
            .stage-btn:hover {{
                transform: none;
                box-shadow: none;
            }}
            
            .abstract-toggle:hover {{
                color: #667eea;
            }}
            
            .paper-card:hover {{
                transform: none;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }}
            
            .paper-title a:hover {{
                color: #2c3e50;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎓 {title}</h1>
            <div class="timestamp">Generated on {timestamp}</div>
        </header>
        
        <div class="controls">
            <div class="stage-selector">
                <button class="stage-btn" data-stage="all">
                    All Papers ({stage1_total})
                </button>
                <button class="stage-btn" data-stage="1">
                    Stage 1+ ({stage1_passed})
                </button>
                <button class="stage-btn" data-stage="2">
                    Stage 2+ ({stage2_passed})
                </button>
                <button class="stage-btn" data-stage="3">
                    Stage 3 ({stage3_passed})
                </button>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <span>Total:</span>
                    <span class="stat-value" id="visible-count">{stage1_total}</span>
                </div>
                <div class="stat">
                    <span>Showing:</span>
                    <span class="stat-value" id="showing-stage">All Papers</span>
                </div>
            </div>
        </div>
        
        <div class="papers-container" id="papers-container">
            <!-- Papers will be rendered here by JavaScript -->
        </div>
        
        <footer>
            <p>{title} | Three-Stage Progressive Filtering System</p>
            <p>Stage 1: Title + Categories | Stage 2: + Authors + Abstract | Stage 3: + Full Paper Analysis</p>
        </footer>
    </div>
    
    <script>
        // Papers data
        const papersData = {papers_json};
        
        // Default stage (highest non-empty stage)
        const defaultStage = '{default_stage}';
        
        // Current filter
        let currentStage = defaultStage;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            setActiveStage(currentStage);
            renderPapers();
            setupEventListeners();
        }});
        
        // Setup event listeners
        function setupEventListeners() {{
            const stageBtns = document.querySelectorAll('.stage-btn');
            stageBtns.forEach(btn => {{
                btn.addEventListener('click', () => {{
                    const stage = btn.dataset.stage;
                    setActiveStage(stage);
                    renderPapers();
                }});
            }});
        }}
        
        // Set active stage
        function setActiveStage(stage) {{
            currentStage = stage;
            
            // Update button states
            document.querySelectorAll('.stage-btn').forEach(btn => {{
                btn.classList.toggle('active', btn.dataset.stage === stage);
            }});
            
            // Update showing text
            const showingStageEl = document.getElementById('showing-stage');
            const stageNames = {{
                'all': 'All Papers',
                '1': 'Stage 1+',
                '2': 'Stage 2+',
                '3': 'Stage 3'
            }};
            showingStageEl.textContent = stageNames[stage];
        }}
        
        // Filter papers based on current stage
        function getFilteredPapers() {{
            if (currentStage === 'all') {{
                return papersData;
            }}
            
            const minStage = parseInt(currentStage);
            return papersData.filter(paper => paper.max_stage >= minStage);
        }}
        
        // Render papers
        function renderPapers() {{
            const container = document.getElementById('papers-container');
            const filteredPapers = getFilteredPapers();
            
            // Update count
            document.getElementById('visible-count').textContent = filteredPapers.length;
            
            if (filteredPapers.length === 0) {{
                container.innerHTML = `
                    <div class="no-papers">
                        <div class="no-papers-icon">📭</div>
                        <h2>No papers found</h2>
                        <p>Try selecting a different filter</p>
                    </div>
                `;
                return;
            }}
            
            container.innerHTML = filteredPapers.map(paper => renderPaper(paper)).join('');
        }}
        
        // Render single paper
        function renderPaper(paper) {{
            const maxStage = paper.max_stage;
            const stageBadges = [];
            
            if (maxStage >= 1) stageBadges.push('<span class="stage-badge stage-1">Stage 1</span>');
            if (maxStage >= 2) stageBadges.push('<span class="stage-badge stage-2">Stage 2</span>');
            if (maxStage >= 3) stageBadges.push('<span class="stage-badge stage-3">Stage 3</span>');
            
            // Determine which stage result to show
            let mainResult = paper.stage1;
            let showScores = false;
            let showCustomFields = false;
            
            if (paper.stage3) {{
                mainResult = paper.stage3;
                showScores = true;
                showCustomFields = true;
            }} else if (paper.stage2) {{
                mainResult = paper.stage2;
            }}
            
            // Build HTML
            let html = `
                <div class="paper-card visible">
                    <div class="paper-header">
                        <div class="paper-title">
                            <a href="${{paper.abs_url}}" target="_blank">${{escapeHtml(paper.title)}}</a>
                        </div>
                        <div class="stage-badges">
                            ${{stageBadges.join('')}}
                        </div>
                    </div>
                    
                    <div class="paper-meta">
                        <div class="authors">
                            <strong>Authors:</strong> ${{paper.authors.join(', ')}}
                        </div>
                        <div class="categories">
                            <strong>Categories:</strong>
                            ${{paper.categories.map(cat => `<span class="category-tag">${{cat}}</span>`).join('')}}
                        </div>
                    </div>
            `;
            
            // Add abstract toggle button and content if stage 2+
            if (paper.stage2 || paper.stage3) {{
                const abstractId = `abstract-${{paper.arxiv_id.replace(/[./]/g, '-')}}`;
                html += `
                    <button class="abstract-toggle" onclick="toggleAbstract('${{abstractId}}', this)">
                        <span class="abstract-toggle-icon">▶</span>
                        <span>Abstract</span>
                    </button>
                    <div class="paper-abstract" id="${{abstractId}}">
                        ${{escapeHtml(paper.abstract)}}
                    </div>
                `;
            }}
            
            // Add scores if stage 3
            if (showScores && paper.stage3) {{
                html += `
                    <div class="scores">
                        <div class="score-item">
                            <span class="score-label">Overall:</span>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${{paper.stage3.score * 100}}%"></div>
                            </div>
                            <span class="score-value">${{paper.stage3.score.toFixed(2)}}</span>
                        </div>
                        <div class="score-item">
                            <span class="score-label">Novelty:</span>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${{paper.stage3.novelty_score * 100}}%"></div>
                            </div>
                            <span class="score-value">${{paper.stage3.novelty_score.toFixed(2)}}</span>
                        </div>
                        <div class="score-item">
                            <span class="score-label">Impact:</span>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${{paper.stage3.impact_score * 100}}%"></div>
                            </div>
                            <span class="score-value">${{paper.stage3.impact_score.toFixed(2)}}</span>
                        </div>
                        <div class="score-item">
                            <span class="score-label">Quality:</span>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${{paper.stage3.quality_score * 100}}%"></div>
                            </div>
                            <span class="score-value">${{paper.stage3.quality_score.toFixed(2)}}</span>
                        </div>
                    </div>
                `;
            }}
            
            // Add reasoning
            if (mainResult.reasoning) {{
                html += `
                    <div class="reasoning">
                        <div class="reasoning-title">Analysis:</div>
                        <div class="reasoning-text">${{escapeHtml(mainResult.reasoning)}}</div>
                    </div>
                `;
            }}
            
            // Add custom fields if stage 3
            if (showCustomFields && paper.stage3 && paper.stage3.custom_fields) {{
                html += '<div class="custom-fields">';
                for (const [key, value] of Object.entries(paper.stage3.custom_fields)) {{
                    html += `
                        <div class="custom-field">
                            <div class="custom-field-title">${{formatFieldName(key)}}:</div>
                            <div class="custom-field-content">${{escapeHtml(value)}}</div>
                        </div>
                    `;
                }}
                html += '</div>';
            }}
            
            html += '</div>';
            return html;
        }}
        
        // Toggle abstract visibility
        function toggleAbstract(abstractId, button) {{
            const abstractEl = document.getElementById(abstractId);
            const isExpanded = abstractEl.classList.contains('expanded');
            
            if (isExpanded) {{
                abstractEl.classList.remove('expanded');
                button.classList.remove('expanded');
            }} else {{
                abstractEl.classList.add('expanded');
                button.classList.add('expanded');
            }}
        }}
        
        // Utility functions
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        function formatFieldName(name) {{
            return name.split('_').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
        }}
    </script>
</body>
</html>"""

