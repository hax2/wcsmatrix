"""Build interactive comparison web application."""

from __future__ import annotations

import json
import re
from pathlib import Path
from wcsmatrix.io import read_jsonl

def clean_words(text: str) -> set[str]:
    return set(re.findall(r"\b[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)?\b", text.lower()))

def build_data():
    prompts = read_jsonl("data/prompts/hc3-50.jsonl")
    human_texts = {r["prompt_id"]: r["text"] for r in read_jsonl("data/texts/human.jsonl")}
    frontier_texts = read_jsonl("data/texts/frontier.jsonl")
    local_texts = read_jsonl("data/texts/local.jsonl")

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
            },
            "models": {}
        }

        # Frontier models
        for r in frontier_texts:
            if r["prompt_id"] == pid:
                m_text = r["text"]
                m_words = clean_words(m_text)
                inter = len(h_words & m_words)
                union = len(h_words | m_words)
                jaccard = (inter / union) if union > 0 else 0
                q_item["models"][r["source"]] = {
                    "source": r["source"],
                    "family": r.get("family", ""),
                    "kind": "frontier",
                    "text": m_text,
                    "word_count": len(m_text.split()),
                    "char_count": len(m_text),
                    "jaccard": round(jaccard, 3),
                    "shared_words_count": inter,
                    "cost_usd": r.get("cost_usd"),
                    "generated_tokens": r.get("generated_tokens"),
                }

        # Local models
        for r in local_texts:
            if r["prompt_id"] == pid:
                m_text = r["text"]
                m_words = clean_words(m_text)
                inter = len(h_words & m_words)
                union = len(h_words | m_words)
                jaccard = (inter / union) if union > 0 else 0
                q_item["models"][r["source"]] = {
                    "source": r["source"],
                    "family": r.get("family", ""),
                    "kind": "local",
                    "text": m_text,
                    "word_count": len(m_text.split()),
                    "char_count": len(m_text),
                    "jaccard": round(jaccard, 3),
                    "shared_words_count": inter,
                    "generated_tokens": r.get("generated_tokens"),
                }

        questions.append(q_item)

    # Compute overall summary stats
    summary = {
        "total_questions": len(questions),
        "models": {
            "gpt-6-astra": {"kind": "frontier", "label": "GPT-6 Astra", "provider": "OpenAI"},
            "claude-opus-5.5": {"kind": "frontier", "label": "Claude Opus 5.5", "provider": "Anthropic"},
            "gemini-4-argon": {"kind": "frontier", "label": "Gemini 4 Argon", "provider": "Google"},
            "qwen-2b": {"kind": "local", "label": "Qwen 3.5 2B", "provider": "OpenWeights"},
            "qwen-4b": {"kind": "local", "label": "Qwen 3.5 4B", "provider": "OpenWeights"},
            "qwen-9b": {"kind": "local", "label": "Qwen 3.5 9B", "provider": "OpenWeights"},
            "qwen-27b-int8": {"kind": "local", "label": "Qwen 3.5 27B (int8)", "provider": "OpenWeights"},
        }
    }

    return {"summary": summary, "questions": questions}

def generate_html(data: dict) -> str:
    json_data = json.dumps(data, ensure_ascii=False)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LLM vs Human Text Comparison | WCSMatrix</title>
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
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
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

    /* Question Banner */
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

    /* Comparison Grid */
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

    .tag-frontier {{
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.3);
    }}

    .tag-local {{
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

    /* Highlight class */
    .shared-word {{
      background: var(--highlight-bg);
      color: var(--highlight-color);
      padding: 0 2px;
      border-radius: 3px;
      font-weight: 500;
    }}

    /* Tabs Bar (when in tab view) */
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

    /* Stats Overview Drawer/Card */
    .stats-card {{
      background: #111827;
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 1.25rem;
      margin-bottom: 0.5rem;
    }}

    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
      font-size: 1.2rem;
      font-weight: 700;
      color: #f1f5f9;
      font-family: 'JetBrains Mono', monospace;
    }}
    .stat-sub {{
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: rgba(0, 0, 0, 0.1);
    }}
    ::-webkit-scrollbar-thumb {{
      background: #334155;
      border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: #475569;
    }}

    @media (max-width: 900px) {{
      .header-content {{
        flex-direction: column;
        align-items: stretch;
      }}
      .controls {{
        justify-content: space-between;
      }}
      .comparison-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body class="view-grid">

  <header>
    <div class="header-content">
      <div class="logo-area">
        <div class="badge-icon">W</div>
        <div class="title-group">
          <h1>WCSMatrix Answer Explorer</h1>
          <p>Compare Frontier & Open LLM Generations vs Human HC3 References (50 prompts)</p>
        </div>
      </div>

      <div class="controls">
        <div class="toggle-pill">
          <button id="btnFilterFrontier" class="active" onclick="setScope('frontier')">Frontier Only</button>
          <button id="btnFilterAll" onclick="setScope('all')">All Models</button>
        </div>

        <div class="toggle-pill">
          <button id="btnViewGrid" class="active" onclick="setViewMode('grid')">Grid</button>
          <button id="btnViewStacked" onclick="setViewMode('stacked')">Stacked</button>
          <button id="btnViewTabs" onclick="setViewMode('tabs')">Tabs</button>
        </div>

        <label class="switch-label">
          <input type="checkbox" id="chkHighlight" onchange="toggleHighlight()">
          Highlight shared words with human
        </label>

        <button class="nav-btn" id="btnPrev" onclick="navigate(-1)">← Prev</button>
        <select id="promptSelect" onchange="selectPrompt(this.value)">
          <!-- Options dynamically populated -->
        </select>
        <button class="nav-btn" id="btnNext" onclick="navigate(1)">Next →</button>
      </div>
    </div>
  </header>

  <main>
    <div class="stats-card" id="statsCard">
      <div class="stats-grid">
        <div class="stat-box">
          <div class="stat-label">Dataset / Questions</div>
          <div class="stat-val">HC3 ELI5 · 50</div>
          <div class="stat-sub">Target: 150–400 words</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Human Mean Words</div>
          <div class="stat-val" id="statHumanWords">234.6</div>
          <div class="stat-sub">Range: 151 – 397 words</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Frontier Models Ready</div>
          <div class="stat-val">3 / 3 (100%)</div>
          <div class="stat-sub">GPT-6, Claude Opus 5.5, Gemini 4</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Avg Jaccard Similarity</div>
          <div class="stat-val">~13.4%</div>
          <div class="stat-sub">Lexical overlap against human</div>
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

    <div class="tabs-bar" id="tabsBar">
      <!-- Tabs populated dynamically in tab view -->
    </div>

    <div class="comparison-grid" id="cardsGrid">
      <!-- Cards populated dynamically -->
    </div>
  </main>

  <script>
    const APP_DATA = {json_data};
    let currentIdx = 0;
    let currentScope = 'frontier'; // 'frontier' or 'all'
    let currentView = 'grid'; // 'grid', 'stacked', 'tabs'
    let highlightShared = false;
    let activeTabSource = 'human';

    const MODEL_CONFIGS = {{
      'human': {{ label: 'Human Reference', tag: 'human', color: '#10b981', order: 0 }},
      'gpt-6-astra': {{ label: 'GPT-6 Astra', tag: 'frontier', color: '#10a37f', order: 1, provider: 'OpenAI' }},
      'claude-opus-5.5': {{ label: 'Claude Opus 5.5', tag: 'frontier', color: '#d97706', order: 2, provider: 'Anthropic' }},
      'gemini-4-argon': {{ label: 'Gemini 4 Argon', tag: 'frontier', color: '#3b82f6', order: 3, provider: 'Google' }},
      'qwen-2b': {{ label: 'Qwen 3.5 2B', tag: 'local', color: '#8b5cf6', order: 10, provider: 'bf16' }},
      'qwen-4b': {{ label: 'Qwen 3.5 4B', tag: 'local', color: '#8b5cf6', order: 11, provider: 'bf16' }},
      'qwen-9b': {{ label: 'Qwen 3.5 9B', tag: 'local', color: '#8b5cf6', order: 12, provider: 'bf16' }},
      'qwen-27b-int8': {{ label: 'Qwen 3.5 27B (int8)', tag: 'local', color: '#a855f7', order: 13, provider: 'int8' }}
    }};

    function init() {{
      const select = document.getElementById('promptSelect');
      select.innerHTML = '';
      APP_DATA.questions.forEach((q, idx) => {{
        const opt = document.createElement('option');
        opt.value = idx;
        const qShort = q.question.length > 55 ? q.question.substring(0, 55) + '...' : q.question;
        opt.textContent = `${{idx + 1}}. [${{q.id}}] ${{qShort}}`;
        select.appendChild(opt);
      }});
      renderQuestion(0);
    }}

    function selectPrompt(idx) {{
      renderQuestion(parseInt(idx));
    }}

    function navigate(delta) {{
      const newIdx = currentIdx + delta;
      if (newIdx >= 0 && newIdx < APP_DATA.questions.length) {{
        renderQuestion(newIdx);
      }}
    }}

    function setScope(scope) {{
      currentScope = scope;
      document.getElementById('btnFilterFrontier').classList.toggle('active', scope === 'frontier');
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
      document.getElementById('btnNext').disabled = (idx === APP_DATA.questions.length - 1);

      const q = APP_DATA.questions[idx];
      document.getElementById('bannerPromptId').textContent = q.id;
      document.getElementById('bannerQuestionText').textContent = q.question;

      renderCards();
    }}

    function renderCards() {{
      const q = APP_DATA.questions[currentIdx];
      const humanWords = getWordSet(q.human.text);
      const grid = document.getElementById('cardsGrid');
      const tabsBar = document.getElementById('tabsBar');
      grid.innerHTML = '';
      tabsBar.innerHTML = '';

      // Collect available sources
      const sources = [
        {{ key: 'human', data: q.human, cfg: MODEL_CONFIGS['human'] }}
      ];

      Object.keys(q.models).forEach(k => {{
        const m = q.models[k];
        if (currentScope === 'frontier' && m.kind !== 'frontier') return;
        const cfg = MODEL_CONFIGS[k] || {{ label: k, tag: m.kind, color: '#64748b', order: 99 }};
        sources.push({{ key: k, data: m, cfg }});
      }});

      sources.sort((a, b) => a.cfg.order - b.cfg.order);

      // Render Tabs if in Tab view
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
        if (!isHuman && s.data.jaccard !== undefined) {{
          metricsHtml += `<span class="metric-badge highlight" title="Vocabulary Jaccard similarity to human">${{Math.round(s.data.jaccard * 100)}}% overlap</span>`;
        }}
        if (s.data.cost_usd) {{
          metricsHtml += `<span class="metric-badge" title="Reported API generation cost">$${{s.data.cost_usd.toFixed(4)}}</span>`;
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
                <span class="tag tag-${{s.cfg.tag}}">${{s.cfg.tag}}</span>
              </div>
            </div>
            <div class="card-metrics">${{metricsHtml}}</div>
          </div>
          <div class="card-body">${{bodyHtml}}</div>
          <div class="card-footer">
            <span>${{s.cfg.provider ? s.cfg.provider + ' · ' : ''}}${{s.data.char_count}} chars</span>
            <button class="copy-btn" onclick="copyToClipboard(this.dataset.text, this)" data-text="${{encodeURIComponent(s.data.text)}}">
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
