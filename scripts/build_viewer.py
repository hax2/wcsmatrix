"""Build interactive comparison web application for ELI5 and Wiki CS/AI across all 3 generator tiers."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from wcsmatrix.io import read_jsonl


def clean_words(text: str) -> set[str]:
    return set(re.findall(r"\b[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)?\b", text.lower()))


def load_prompt_wcs(scores_path: str) -> dict[tuple[str, str], float]:
    """Return mean realistic p=0.99 WCS across complete scorers for (prompt_id, source)."""
    path = Path(scores_path)
    if not path.exists():
        return {}
    by_cell: dict[tuple[str, str], list[float]] = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["mode"] == "realistic" and float(row["p"]) == 0.99 and row["scorer"] != "qwen-27b-int8":
                key = (row["prompt_id"], row["source"])
                by_cell.setdefault(key, []).append(float(row["wcs"]))
    return {k: round(sum(v) / len(v), 4) for k, v in by_cell.items() if v}


def build_domain_questions(
    prompts_path: str,
    human_path: str,
    closed_frontier_path: str,
    open_frontier_path: str,
    local_path: str,
    scores_path: str,
) -> list[dict]:
    prompts = read_jsonl(prompts_path)
    human_texts = {r["prompt_id"]: r["text"] for r in read_jsonl(human_path)}
    closed_frontier = read_jsonl(closed_frontier_path) if Path(closed_frontier_path).exists() else []
    open_frontier = read_jsonl(open_frontier_path) if Path(open_frontier_path).exists() else []
    local_texts = read_jsonl(local_path) if Path(local_path).exists() else []
    wcs_lookup = load_prompt_wcs(scores_path)

    questions = []
    for p in prompts:
        pid = p["id"]
        h_text = human_texts.get(pid, "")
        h_words = clean_words(h_text)
        h_len = len(h_text.split())

        q_item = {
            "id": pid,
            "question": p["question"],
            "prompt": p["prompt"],
            "domain": p.get("domain", "reddit_eli5"),
            "human": {
                "text": h_text,
                "word_count": h_len,
                "char_count": len(h_text),
                "wcs_099": wcs_lookup.get((pid, "human")),
            },
            "models": {},
        }

        for tier_tag, rows in [
            ("frontier_proprietary", closed_frontier),
            ("large_open_weight", open_frontier),
            ("small_open_weight", local_texts),
        ]:
            for r in rows:
                if r["prompt_id"] == pid:
                    m_text = r["text"]
                    m_words = clean_words(m_text)
                    inter = len(h_words & m_words)
                    union = len(h_words | m_words)
                    jaccard = (inter / union) if union > 0 else 0
                    q_item["models"][r["source"]] = {
                        "source": r["source"],
                        "family": r.get("family", ""),
                        "kind": r.get("kind", "frontier"),
                        "tier": tier_tag,
                        "text": m_text,
                        "word_count": len(m_text.split()),
                        "char_count": len(m_text),
                        "jaccard": round(jaccard, 3),
                        "shared_words_count": inter,
                        "cost_usd": r.get("cost_usd"),
                        "generated_tokens": r.get("generated_tokens"),
                        "wcs_099": wcs_lookup.get((pid, r["source"])),
                    }

        questions.append(q_item)
    return questions


def build_data() -> dict:
    eli5_questions = build_domain_questions(
        prompts_path="data/prompts/hc3-50.jsonl",
        human_path="data/texts/human.jsonl",
        closed_frontier_path="data/texts/frontier.jsonl",
        open_frontier_path="data/texts/open-frontier-20261030.jsonl",
        local_path="data/texts/local.jsonl",
        scores_path="results/reports/hc3-50-comparison-open-frontier-20261030/prompt-scores.csv",
    )
    wiki_questions = build_domain_questions(
        prompts_path="data/prompts/hc3-wiki-50.jsonl",
        human_path="data/texts/wiki-human.jsonl",
        closed_frontier_path="data/texts/wiki-closed-frontier-20261030.jsonl",
        open_frontier_path="data/texts/wiki-open-frontier-20261030.jsonl",
        local_path="data/texts/wiki-local.jsonl",
        scores_path="results/reports/hc3-wiki-50-comparison-frontier-20261030/prompt-scores.csv",
    )
    all_questions = eli5_questions + wiki_questions

    summary = {
        "total_questions": len(all_questions),
        "eli5_questions": len(eli5_questions),
        "wiki_questions": len(wiki_questions),
    }

    return {"summary": summary, "questions": all_questions}


def generate_html(data: dict) -> str:
    json_data = json.dumps(data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Whose Words Are Reachable? | WCSMatrix Explorer</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: #1f293d;
      --card-hover: #1a2333;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --accent-human: #10b981;
      --accent-human-bg: rgba(16, 185, 129, 0.12);
      --accent-openai: #10a37f;
      --accent-claude: #d97706;
      --accent-gemini: #3b82f6;
      --accent-large-ow: #ec4899;
      --accent-local: #8b5cf6;
      --highlight-bg: #854d0e;
      --highlight-color: #fef08a;
      --radius: 12px;
      --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text-main);
      line-height: 1.6;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    header {{
      background: rgba(17, 24, 39, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border);
      position: sticky;
      top: 0;
      z-index: 50;
      padding: 1rem 1.5rem;
    }}

    .header-content {{
      max-width: 1600px;
      margin: 0 auto;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }}

    .logo-area {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}

    .badge-icon {{
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: linear-gradient(135deg, #3b82f6, #ec4899);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1rem;
      color: white;
    }}

    .title-group h1 {{
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}

    .title-group p {{
      font-size: 0.8rem;
      color: var(--text-muted);
    }}

    .controls {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }}

    .nav-btn {{
      background: var(--card-border);
      border: 1px solid #334155;
      color: var(--text-main);
      padding: 0.45rem 0.85rem;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      transition: var(--transition);
    }}
    .nav-btn:hover:not(:disabled) {{
      background: #334155;
      border-color: #475569;
    }}
    .nav-btn:disabled {{
      opacity: 0.4;
      cursor: not-allowed;
    }}

    select, input[type="text"] {{
      background: #1e293b;
      border: 1px solid #334155;
      color: var(--text-main);
      padding: 0.45rem 0.85rem;
      border-radius: 8px;
      font-size: 0.85rem;
      outline: none;
      transition: var(--transition);
    }}
    select:focus, input[type="text"]:focus {{
      border-color: #3b82f6;
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }}

    .toggle-pill {{
      display: flex;
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 2px;
    }}

    .toggle-pill button {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      transition: var(--transition);
    }}

    .toggle-pill button.active {{
      background: #3b82f6;
      color: white;
    }}

    .switch-label {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.82rem;
      color: var(--text-muted);
      cursor: pointer;
      user-select: none;
    }}
    .switch-label input {{
      cursor: pointer;
      accent-color: #f59e0b;
    }}

    main {{
      max-width: 1600px;
      width: 100%;
      margin: 0 auto;
      padding: 1.5rem;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }}

    .question-banner {{
      background: linear-gradient(180deg, #131d2e 0%, var(--card-bg) 100%);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 1.5rem;
      position: relative;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }}

    .q-meta {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 0.6rem;
    }}

    .q-badge {{
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 0.2rem 0.6rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 500;
    }}

    .q-instruction {{
      font-size: 0.8rem;
      color: var(--text-dim);
    }}

    .question-text {{
      font-size: 1.25rem;
      font-weight: 600;
      color: #f8fafc;
      letter-spacing: -0.01em;
    }}

    .comparison-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 1.25rem;
    }}

    .view-stacked .comparison-grid {{
      grid-template-columns: 1fr;
    }}

    .view-tabs .comparison-grid {{
      grid-template-columns: 1fr;
    }}

    .model-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: var(--transition);
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}

    .model-card:hover {{
      border-color: #334155;
      transform: translateY(-2px);
    }}

    .model-card.human-card {{
      border-color: rgba(16, 185, 129, 0.4);
      background: linear-gradient(180deg, rgba(16, 185, 129, 0.05) 0%, var(--card-bg) 100%);
    }}

    .card-header {{
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      background: rgba(15, 23, 42, 0.4);
    }}

    .model-info {{
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }}

    .model-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }}

    .model-name {{
      font-weight: 600;
      font-size: 0.95rem;
    }}

    .tag {{
      font-size: 0.7rem;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.04em;
    }}

    .tag-human {{
      background: var(--accent-human-bg);
      color: var(--accent-human);
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}

    .tag-frontier_proprietary {{
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.3);
    }}

    .tag-large_open_weight {{
      background: rgba(236, 72, 153, 0.15);
      color: #f472b6;
      border: 1px solid rgba(236, 72, 153, 0.3);
    }}

    .tag-small_open_weight {{
      background: rgba(139, 92, 246, 0.15);
      color: #a78bfa;
      border: 1px solid rgba(139, 92, 246, 0.3);
    }}

    .card-metrics {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}

    .metric-badge {{
      font-size: 0.75rem;
      padding: 0.2rem 0.5rem;
      border-radius: 6px;
      background: #1e293b;
      color: var(--text-muted);
      border: 1px solid #293548;
      font-family: 'JetBrains Mono', monospace;
    }}

    .metric-badge.highlight {{
      background: rgba(245, 158, 11, 0.15);
      color: #fbbf24;
      border-color: rgba(245, 158, 11, 0.3);
    }}

    .metric-badge.wcs-badge {{
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border-color: rgba(16, 185, 129, 0.3);
    }}

    .card-body {{
      padding: 1.25rem;
      flex: 1;
      font-size: 0.92rem;
      color: #cbd5e1;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.7;
      max-height: 520px;
      overflow-y: auto;
    }}

    .card-footer {{
      padding: 0.75rem 1.25rem;
      border-top: 1px solid var(--card-border);
      background: rgba(15, 23, 42, 0.2);
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.78rem;
      color: var(--text-dim);
    }}

    .copy-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 0.25rem 0.6rem;
      border-radius: 6px;
      font-size: 0.75rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.3rem;
      transition: var(--transition);
    }}
    .copy-btn:hover {{
      background: #1e293b;
      border-color: #334155;
      color: var(--text-main);
    }}

    .shared-word {{
      background: var(--highlight-bg);
      color: var(--highlight-color);
      padding: 0 2px;
      border-radius: 3px;
      font-weight: 500;
    }}

    .tabs-bar {{
      display: none;
      gap: 0.5rem;
      overflow-x: auto;
      padding-bottom: 0.5rem;
      margin-bottom: 0.5rem;
    }}

    .view-tabs .tabs-bar {{
      display: flex;
    }}

    .tab-btn {{
      background: #1e293b;
      border: 1px solid #334155;
      color: var(--text-muted);
      padding: 0.5rem 1rem;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      white-space: nowrap;
      transition: var(--transition);
    }}
    .tab-btn:hover {{
      background: #273549;
    }}
    .tab-btn.active {{
      background: #3b82f6;
      color: white;
      border-color: #3b82f6;
    }}

    .stats-card {{
      background: #111827;
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 1.25rem;
      margin-bottom: 0.5rem;
    }}

    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
    }}

    .stat-box {{
      background: #1e293b;
      border: 1px solid #293548;
      border-radius: 8px;
      padding: 0.85rem 1rem;
    }}
    .stat-label {{
      font-size: 0.75rem;
      color: var(--text-dim);
      margin-bottom: 0.25rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .stat-val {{
      font-size: 1.15rem;
      font-weight: 700;
      color: #f1f5f9;
      font-family: 'JetBrains Mono', monospace;
    }}
    .stat-sub {{
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
    }}
  </style>
</head>
<body class="view-grid">

  <header>
    <div class="header-content">
      <div class="logo-area">
        <div class="badge-icon">W</div>
        <div class="title-group">
          <h1>Whose Words Are Reachable? · WCSMatrix Explorer</h1>
          <p>Human Writing, Proprietary Frontier, Large Open-Weight (427B–2.78T), and Small Open-Weight Models</p>
        </div>
      </div>

      <div class="controls">
        <div class="toggle-pill">
          <button id="btnDomainEli5" class="active" onclick="setDomain('reddit_eli5')">ELI5 (50)</button>
          <button id="btnDomainWiki" onclick="setDomain('wiki_csai')">Wiki CS/AI (50)</button>
        </div>

        <div class="toggle-pill">
          <button id="btnFilterFrontier" class="active" onclick="setScope('frontier_all')">Frontier (10)</button>
          <button id="btnFilterClosed" onclick="setScope('frontier_proprietary')">Closed (3)</button>
          <button id="btnFilterLargeOW" onclick="setScope('large_open_weight')">Large OW (7)</button>
          <button id="btnFilterAll" onclick="setScope('all')">All (18)</button>
        </div>

        <div class="toggle-pill">
          <button id="btnViewGrid" class="active" onclick="setViewMode('grid')">Grid</button>
          <button id="btnViewStacked" onclick="setViewMode('stacked')">Stacked</button>
          <button id="btnViewTabs" onclick="setViewMode('tabs')">Tabs</button>
        </div>

        <label class="switch-label">
          <input type="checkbox" id="chkHighlight" onchange="toggleHighlight()">
          Highlight shared words
        </label>

        <button class="nav-btn" id="btnPrev" onclick="navigate(-1)">← Prev</button>
        <select id="promptSelect" onchange="selectPrompt(this.value)"></select>
        <button class="nav-btn" id="btnNext" onclick="navigate(1)">Next →</button>
      </div>
    </div>
  </header>

  <main>
    <div class="stats-card" id="statsCard">
      <div class="stats-grid">
        <div class="stat-box">
          <div class="stat-label">Human Reachability (p=0.99)</div>
          <div class="stat-val" id="statHumanWcs">0.8118 (ELI5) · 0.8233 (Wiki)</div>
          <div class="stat-sub">Lowest reachability under small scorers</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Proprietary Frontier (3)</div>
          <div class="stat-val">0.8438 (ELI5) · 0.8638 (Wiki)</div>
          <div class="stat-sub">GPT-6 Astra, Claude Opus 5.5, Gemini 4 Argon</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Large Open-Weight (7, 427B–2.78T)</div>
          <div class="stat-val">0.8672 (ELI5) · 0.8876 (Wiki)</div>
          <div class="stat-sub">DeepSeek-V4/V4.1, Qwen3.8-2.4T, Kimi-K3, GLM-5.3, MiniMax-M3, MiMo-V2.6</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Small Open-Weight (≤27B)</div>
          <div class="stat-val">0.9466 (ELI5) · 0.9501 (Wiki)</div>
          <div class="stat-sub">Qwen 3.5 (2B–27B) & Gemma 4 (E2B–12B)</div>
        </div>
      </div>
    </div>

    <div class="question-banner">
      <div class="q-meta">
        <span class="q-badge" id="bannerPromptId">hc3-eli5-0</span>
        <span class="q-instruction">Prompt: "Answer the following question in English, using 150–400 words. Give only your answer."</span>
      </div>
      <div class="question-text" id="bannerQuestionText">Loading question...</div>
    </div>

    <div class="tabs-bar" id="tabsBar"></div>
    <div class="comparison-grid" id="cardsGrid"></div>
  </main>

  <script>
    const APP_DATA = {json_data};
    let currentDomain = 'reddit_eli5';
    let filteredQuestions = [];
    let currentIdx = 0;
    let currentScope = 'frontier_all';
    let currentView = 'grid';
    let highlightShared = false;
    let activeTabSource = 'human';

    const MODEL_CONFIGS = {{
      'human': {{ label: 'Human Reference', tag: 'human', tagLabel: 'Human', color: '#10b981', order: 0 }},
      'gpt-6-astra': {{ label: 'GPT-6 Astra', tag: 'frontier_proprietary', tagLabel: 'Proprietary Frontier', color: '#10a37f', order: 1, provider: 'OpenAI' }},
      'claude-opus-5.5': {{ label: 'Claude Opus 5.5', tag: 'frontier_proprietary', tagLabel: 'Proprietary Frontier', color: '#d97706', order: 2, provider: 'Anthropic' }},
      'gemini-4-argon': {{ label: 'Gemini 4 Argon', tag: 'frontier_proprietary', tagLabel: 'Proprietary Frontier', color: '#3b82f6', order: 3, provider: 'Google' }},
      'deepseek-v4.1-flash-1017': {{ label: 'DeepSeek-V4.1-Flash (763B)', tag: 'large_open_weight', tagLabel: 'Large Open-Weight', color: '#ec4899', order: 4, provider: 'DeepSeek · 763B A38B' }},
      'glm-5.3': {{ label: 'GLM-5.3 (753B)', tag: 'large_open_weight', tagLabel: 'Large Open-Weight', color: '#ec4899', order: 5, provider: 'Z.ai · 753B A44B' }},
      'minimax-m3': {{ label: 'MiniMax-M3 (427B)', tag: 'large_open_weight', tagLabel: 'Large Open-Weight', color: '#ec4899', order: 6, provider: 'MiniMax · 427B A22B' }},
      'kimi-k3': {{ label: 'Kimi-K3 (2.78T)', tag: 'large_open_weight', tagLabel: 'Large Open-Weight', color: '#ec4899', order: 7, provider: 'Moonshot · 2.78T A95B' }},
      'mimo-v2.6-pro': {{ label: 'MiMo-V2.6-Pro (1.02T)', tag: 'large_open_weight', tagLabel: 'Large Open-Weight', color: '#ec4899', order: 8, provider: 'Xiaomi · 1.02T A49B' }},
      'deepseek-v4-pro-0813': {{ label: 'DeepSeek-V4-Pro (1.65T)', tag: 'large_open_weight', tagLabel: 'Large Open-Weight', color: '#ec4899', order: 9, provider: 'DeepSeek · 1.65T A72B' }},
      'qwen3.8-2.4t-a95b': {{ label: 'Qwen3.8-2.4T-A95B (2.45T)', tag: 'large_open_weight', tagLabel: 'Large Open-Weight', color: '#ec4899', order: 10, provider: 'Alibaba · 2.45T A95B' }},
      'qwen-2b': {{ label: 'Qwen 3.5 2B', tag: 'small_open_weight', tagLabel: 'Small Open-Weight', color: '#8b5cf6', order: 20, provider: 'Qwen · bf16' }},
      'qwen-4b': {{ label: 'Qwen 3.5 4B', tag: 'small_open_weight', tagLabel: 'Small Open-Weight', color: '#8b5cf6', order: 21, provider: 'Qwen · bf16' }},
      'qwen-9b': {{ label: 'Qwen 3.5 9B', tag: 'small_open_weight', tagLabel: 'Small Open-Weight', color: '#8b5cf6', order: 22, provider: 'Qwen · bf16' }},
      'qwen-27b-int8': {{ label: 'Qwen 3.5 27B (int8)', tag: 'small_open_weight', tagLabel: 'Small Open-Weight', color: '#a855f7', order: 23, provider: 'Qwen · int8' }},
      'gemma-e2b': {{ label: 'Gemma 4 E2B (5.1B)', tag: 'small_open_weight', tagLabel: 'Small Open-Weight', color: '#8b5cf6', order: 24, provider: 'Gemma · bf16' }},
      'gemma-e4b': {{ label: 'Gemma 4 E4B (8.0B)', tag: 'small_open_weight', tagLabel: 'Small Open-Weight', color: '#8b5cf6', order: 25, provider: 'Gemma · bf16' }},
      'gemma-12b': {{ label: 'Gemma 4 12B', tag: 'small_open_weight', tagLabel: 'Small Open-Weight', color: '#8b5cf6', order: 26, provider: 'Gemma · bf16' }}
    }};

    function setDomain(domain) {{
      currentDomain = domain;
      document.getElementById('btnDomainEli5').classList.toggle('active', domain === 'reddit_eli5');
      document.getElementById('btnDomainWiki').classList.toggle('active', domain === 'wiki_csai');
      filteredQuestions = APP_DATA.questions.filter(q => q.domain === domain);
      const select = document.getElementById('promptSelect');
      select.innerHTML = '';
      filteredQuestions.forEach((q, idx) => {{
        const opt = document.createElement('option');
        opt.value = idx;
        const qShort = q.question.length > 55 ? q.question.substring(0, 55) + '...' : q.question;
        opt.textContent = `${{idx + 1}}. [${{q.id}}] ${{qShort}}`;
        select.appendChild(opt);
      }});
      renderQuestion(0);
    }}

    function init() {{
      setDomain('reddit_eli5');
    }}

    function selectPrompt(idx) {{
      renderQuestion(parseInt(idx));
    }}

    function navigate(delta) {{
      const newIdx = currentIdx + delta;
      if (newIdx >= 0 && newIdx < filteredQuestions.length) {{
        renderQuestion(newIdx);
      }}
    }}

    function setScope(scope) {{
      currentScope = scope;
      document.getElementById('btnFilterFrontier').classList.toggle('active', scope === 'frontier_all');
      document.getElementById('btnFilterClosed').classList.toggle('active', scope === 'frontier_proprietary');
      document.getElementById('btnFilterLargeOW').classList.toggle('active', scope === 'large_open_weight');
      document.getElementById('btnFilterAll').classList.toggle('active', scope === 'all');
      renderCards();
    }}

    function setViewMode(mode) {{
      currentView = mode;
      document.body.className = `view-${{mode}}`;
      document.getElementById('btnViewGrid').classList.toggle('active', mode === 'grid');
      document.getElementById('btnViewStacked').classList.toggle('active', mode === 'stacked');
      document.getElementById('btnViewTabs').classList.toggle('active', mode === 'tabs');
      renderCards();
    }}

    function toggleHighlight() {{
      highlightShared = document.getElementById('chkHighlight').checked;
      renderCards();
    }}

    function setActiveTab(sourceKey) {{
      activeTabSource = sourceKey;
      renderCards();
    }}

    function getWordSet(text) {{
      const matches = text.toLowerCase().match(/\\b[a-z0-9]+(?:'[a-z0-9]+)?\\b/g) || [];
      return new Set(matches);
    }}

    function highlightText(text, referenceWordSet) {{
      if (!highlightShared || !referenceWordSet) return escapeHtml(text);
      return text.replace(/\\b[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)?\\b/g, (match) => {{
        if (referenceWordSet.has(match.toLowerCase())) {{
          return `<span class="shared-word">${{escapeHtml(match)}}</span>`;
        }}
        return escapeHtml(match);
      }});
    }}

    function escapeHtml(text) {{
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }}

    function copyToClipboard(text, btnElement) {{
      navigator.clipboard.writeText(text).then(() => {{
        const orig = btnElement.innerHTML;
        btnElement.innerHTML = '✓ Copied!';
        setTimeout(() => {{ btnElement.innerHTML = orig; }}, 1500);
      }});
    }}

    function renderQuestion(idx) {{
      currentIdx = idx;
      document.getElementById('promptSelect').value = idx;
      document.getElementById('btnPrev').disabled = (idx === 0);
      document.getElementById('btnNext').disabled = (idx === filteredQuestions.length - 1);

      const q = filteredQuestions[idx];
      document.getElementById('bannerPromptId').textContent = q.id;
      document.getElementById('bannerQuestionText').textContent = q.question;

      renderCards();
    }}

    function renderCards() {{
      const q = filteredQuestions[currentIdx];
      const humanWords = getWordSet(q.human.text);
      const grid = document.getElementById('cardsGrid');
      const tabsBar = document.getElementById('tabsBar');
      grid.innerHTML = '';
      tabsBar.innerHTML = '';

      const sources = [
        {{ key: 'human', data: q.human, cfg: MODEL_CONFIGS['human'] }}
      ];

      Object.keys(q.models).forEach(k => {{
        const m = q.models[k];
        if (currentScope === 'frontier_all' && m.tier === 'small_open_weight') return;
        if (currentScope === 'frontier_proprietary' && m.tier !== 'frontier_proprietary') return;
        if (currentScope === 'large_open_weight' && m.tier !== 'large_open_weight') return;
        const cfg = MODEL_CONFIGS[k] || {{ label: k, tag: m.tier, tagLabel: m.tier, color: '#64748b', order: 99 }};
        sources.push({{ key: k, data: m, cfg }});
      }});

      sources.sort((a, b) => a.cfg.order - b.cfg.order);

      if (currentView === 'tabs') {{
        sources.forEach(s => {{
          const btn = document.createElement('button');
          btn.className = `tab-btn ${{activeTabSource === s.key ? 'active' : ''}}`;
          btn.innerHTML = `<span style="color: ${{s.cfg.color}}">●</span> ${{s.cfg.label}}`;
          btn.onclick = () => setActiveTab(s.key);
          tabsBar.appendChild(btn);
        }});
      }}

      sources.forEach(s => {{
        if (currentView === 'tabs' && activeTabSource !== s.key) return;

        const isHuman = (s.key === 'human');
        const card = document.createElement('div');
        card.className = `model-card ${{isHuman ? 'human-card' : ''}}`;

        let metricsHtml = `<span class="metric-badge">${{s.data.word_count}} words</span>`;
        if (s.data.wcs_099 !== undefined && s.data.wcs_099 !== null) {{
          metricsHtml += `<span class="metric-badge wcs-badge" title="Mean realistic top-p=0.99 WCS across 6 small scorers">WCS: ${{(s.data.wcs_099 * 100).toFixed(1)}}%</span>`;
        }}
        if (!isHuman && s.data.jaccard !== undefined) {{
          metricsHtml += `<span class="metric-badge highlight" title="Vocabulary Jaccard similarity to human">${{Math.round(s.data.jaccard * 100)}}% overlap</span>`;
        }}

        const bodyHtml = isHuman
          ? escapeHtml(s.data.text)
          : highlightText(s.data.text, humanWords);

        card.innerHTML = `
          <div class="card-header">
            <div class="model-info">
              <div class="model-dot" style="background: ${{s.cfg.color}}"></div>
              <div>
                <span class="model-name">${{s.cfg.label}}</span>
                <span class="tag tag-${{s.cfg.tag}}">${{s.cfg.tagLabel}}</span>
              </div>
            </div>
            <div class="card-metrics">${{metricsHtml}}</div>
          </div>
          <div class="card-body">${{bodyHtml}}</div>
          <div class="card-footer">
            <span>${{s.cfg.provider ? s.cfg.provider + ' · ' : ''}}${{s.data.char_count}} chars</span>
            <button class="copy-btn" onclick="copyToClipboard(this.dataset.text, this)">
              📋 Copy
            </button>
          </div>
        `;

        const copyBtn = card.querySelector('.copy-btn');
        copyBtn.dataset.text = s.data.text;

        grid.appendChild(card);
      }});
    }}

    window.onload = init;
  </script>
</body>
</html>
"""
    return html


def main():
    data = build_data()
    out_dir = Path("web")
    out_dir.mkdir(parents=True, exist_ok=True)

    html = generate_html(data)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"Generated comparison web application at web/index.html ({len(html)} bytes)")


if __name__ == "__main__":
    main()
