"""HTML page builders for the MCP server's web interface.

Two pages are served:
  /        — Dashboard: shows all tools, asset types, and educational resources.
             Intended for developers and demo audiences.
  /editor  — Content editor: a standalone HTML file the boss can download,
             edit offline, and send back. Changes are applied via apply_changes.py.
"""

import html
import json

from context_data import ASSET_TYPE_DESCRIPTIONS, RESOURCES, TOOLS_METADATA

# Maps the risk level label (from content.json) to a badge background color.
RISK_BADGE_COLORS: dict[str, str] = {
    "Aggressive": "#e05c00",
    "Balanced (default)": "#b8960c",
    "Conservative": "#2a7a4b",
    "Very High Risk / Very High Potential": "#8b1a1a",
    "High Risk / Blended": "#5a3e8a",
}


def build_dashboard_html() -> str:
    """Generate the knowledge-base dashboard served at /."""
    asset_cards = ""
    for code, meta in ASSET_TYPE_DESCRIPTIONS.items():
        badge_color = RISK_BADGE_COLORS.get(meta["risk"], "#555")
        asset_cards += f"""
        <div class="card">
          <div class="card-header">
            <span class="code-badge">{html.escape(code)}</span>
            <span class="label">{html.escape(meta['label'])}</span>
            <span class="risk-badge" style="background:{badge_color}">{html.escape(meta['risk'])}</span>
          </div>
          <p>{html.escape(meta['description'])}</p>
        </div>"""

    tool_cards = ""
    for t in TOOLS_METADATA:
        tool_cards += f"""
        <div class="card">
          <div class="card-header">
            <span class="code-badge">{html.escape(t['name'])}</span>
          </div>
          <p>{html.escape(t['description'])}</p>
          <div class="params-line"><span class="params-label">Parameters:</span> {html.escape(t['params'])}</div>
        </div>"""

    resource_tabs_nav = ""
    resource_panels = ""
    for i, (uri, meta) in enumerate(RESOURCES.items()):
        active = "active" if i == 0 else ""
        slug = uri.replace("tontine://", "").replace("-", "_")
        resource_tabs_nav += f'<button class="tab-btn {active}" onclick="showTab(event, \'{slug}\')">{html.escape(meta["name"])}</button>\n'
        display = "block" if i == 0 else "none"
        resource_panels += f"""
        <div id="tab_{slug}" class="tab-panel" style="display:{display}">
          <p class="resource-uri">{html.escape(uri)}</p>
          <div class="markdown-body" id="md_{slug}"></div>
          <script>
            document.getElementById("md_{slug}").innerHTML =
              marked.parse({repr(RESOURCES[uri]['content'])});
          </script>
        </div>"""

    n_tools = len(TOOLS_METADATA)
    n_resources = len(RESOURCES)
    n_assets = len(ASSET_TYPE_DESCRIPTIONS)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tontine MCP Server — Knowledge Base</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  :root {{
    --blue: #1a6fc4;
    --blue-dark: #154f8e;
    --blue-light: #e8f1fb;
    --blue-mid: #d0e4f7;
    --bg: #f5f7fa;
    --surface: #ffffff;
    --surface2: #f0f4f9;
    --border: #d8e3ef;
    --text: #1a2332;
    --muted: #5a6e85;
    --radius: 8px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 15px; line-height: 1.65; }}

  header {{ background: var(--blue); padding: 20px 40px; display: flex; align-items: center; gap: 16px; box-shadow: 0 2px 8px rgba(26,111,196,0.18); }}
  .logo {{ font-size: 24px; font-weight: 700; color: #fff; letter-spacing: -0.3px; }}
  .logo span {{ font-weight: 300; opacity: 0.85; }}
  .tag {{ background: #fff; color: var(--blue); font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; padding: 3px 9px; border-radius: 4px; }}
  .subtitle {{ color: rgba(255,255,255,0.7); font-size: 13px; margin-left: auto; }}

  nav.sections {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 0 40px; display: flex; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  nav.sections a {{ color: var(--muted); text-decoration: none; padding: 14px 20px; font-size: 13px; font-weight: 500; border-bottom: 2px solid transparent; transition: color 0.15s, border-color 0.15s; }}
  nav.sections a:hover {{ color: var(--blue); border-color: var(--blue); }}

  main {{ max-width: 1100px; margin: 0 auto; padding: 40px; }}
  section {{ margin-bottom: 56px; }}
  section h2 {{ font-size: 18px; font-weight: 600; color: var(--blue); border-bottom: 2px solid var(--blue-mid); padding-bottom: 10px; margin-bottom: 24px; }}

  .intro-box {{ background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--blue); border-radius: var(--radius); padding: 20px 24px; margin-bottom: 32px; color: var(--muted); font-size: 14px; line-height: 1.75; }}
  .intro-box strong {{ color: var(--text); }}

  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px 22px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
  .card-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }}
  .code-badge {{ background: var(--blue-light); color: var(--blue-dark); font-family: "SF Mono", "Fira Code", monospace; font-size: 13px; padding: 2px 10px; border-radius: 4px; border: 1px solid var(--blue-mid); font-weight: 600; }}
  .label {{ font-weight: 600; font-size: 15px; color: var(--text); }}
  .risk-badge {{ font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; color: #fff; letter-spacing: 0.3px; }}
  .card p {{ color: var(--muted); font-size: 14px; line-height: 1.65; }}
  .params-line {{ margin-top: 10px; font-size: 13px; color: var(--muted); }}
  .params-label {{ color: var(--blue); font-weight: 600; }}

  .tab-bar {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 20px; }}
  .tab-btn {{ background: var(--surface); border: 1px solid var(--border); color: var(--muted); padding: 7px 15px; border-radius: var(--radius); cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s; }}
  .tab-btn:hover {{ border-color: var(--blue); color: var(--blue); background: var(--blue-light); }}
  .tab-btn.active {{ background: var(--blue); color: #fff; border-color: var(--blue); font-weight: 600; }}

  .tab-panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 28px 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
  .resource-uri {{ font-family: monospace; font-size: 12px; color: var(--muted); margin-bottom: 20px; background: var(--surface2); padding: 4px 10px; border-radius: 4px; display: inline-block; border: 1px solid var(--border); }}

  .markdown-body h1 {{ font-size: 22px; color: var(--blue); margin: 0 0 16px; font-weight: 700; }}
  .markdown-body h2 {{ font-size: 17px; color: var(--text); margin: 24px 0 10px; font-weight: 600; border-bottom: 1px solid var(--border); padding-bottom: 6px; }}
  .markdown-body h3 {{ font-size: 15px; color: var(--blue-dark); margin: 18px 0 8px; font-weight: 600; }}
  .markdown-body p {{ margin-bottom: 12px; color: var(--muted); font-size: 14px; line-height: 1.7; }}
  .markdown-body strong {{ color: var(--text); }}
  .markdown-body em {{ color: var(--blue); font-style: italic; }}
  .markdown-body ul, .markdown-body ol {{ margin: 8px 0 14px 22px; color: var(--muted); font-size: 14px; }}
  .markdown-body li {{ margin-bottom: 5px; line-height: 1.6; }}
  .markdown-body code {{ background: var(--blue-light); color: var(--blue-dark); font-family: monospace; font-size: 12px; padding: 1px 6px; border-radius: 3px; }}
  .markdown-body table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }}
  .markdown-body th {{ background: var(--blue); color: #fff; text-align: left; padding: 10px 14px; font-weight: 600; }}
  .markdown-body td {{ padding: 9px 14px; border-bottom: 1px solid var(--border); color: var(--muted); vertical-align: top; background: var(--surface); }}
  .markdown-body tr:nth-child(even) td {{ background: var(--surface2); }}
  .markdown-body tr:last-child td {{ border-bottom: none; }}

  footer {{ text-align: center; padding: 30px; color: var(--muted); font-size: 12px; border-top: 1px solid var(--border); margin-top: 20px; background: var(--surface); }}
  footer a {{ color: var(--blue); text-decoration: none; }}
</style>
</head>
<body>

<header>
  <div class="logo">Tontine<span>Trust</span></div>
  <span class="tag">MCP Server</span>
  <span class="subtitle">Knowledge Base &mdash; what the AI knows</span>
</header>

<nav class="sections">
  <a href="#about">About</a>
  <a href="#tools">Tools</a>
  <a href="#assets">Assets</a>
  <a href="#resources">Resources</a>
</nav>

<main>
  <section id="about">
    <h2>About This MCP Server</h2>
    <div class="intro-box">
      <strong>What is MCP?</strong> The Model Context Protocol (MCP) is an open standard by Anthropic
      that lets AI assistants like Claude call external tools and read structured knowledge bases.
      Instead of giving vague generic answers about retirement income, the AI can call this server
      to get <strong>real numbers</strong> from the Tontinator calculator and <strong>accurate context</strong>
      about how Tontine Trust works.<br><br>
      <strong>What does this server expose?</strong> <strong>{n_tools} tools</strong> (for calculations and information retrieval),
      <strong>{n_assets} asset types</strong>, and <strong>{n_resources} educational resources</strong> — markdown documents
      the AI reads to answer questions accurately. All calculation data is powered live by
      <strong>api.mytontine.com</strong>.
    </div>
  </section>

  <section id="tools">
    <h2>Exposed Tools ({n_tools})</h2>
    {tool_cards}
  </section>

  <section id="assets">
    <h2>Asset Types ({n_assets})</h2>
    {asset_cards}
  </section>

  <section id="resources">
    <h2>Educational Resources ({n_resources})</h2>
    <div class="tab-bar">
      {resource_tabs_nav}
    </div>
    {resource_panels}
  </section>
</main>

<footer>
  Tontine Trust MCP Server &mdash;
  <a href="https://tontine.com" target="_blank">tontine.com</a> &mdash;
  API: <a href="https://api.mytontine.com" target="_blank">api.mytontine.com</a>
  &mdash; <a href="/editor">Content Editor</a>
</footer>

<script>
function showTab(event, slug) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab_' + slug).style.display = 'block';
  event.target.classList.add('active');
}}
</script>

</body>
</html>"""


def build_editor_html() -> str:
    """Generate the standalone content editor served at /editor.

    The downloaded file works without a server — the boss opens it by double-clicking,
    edits text directly in the browser, clicks Save, and emails the result back.
    Changes are applied by the developer via: python3 apply_changes.py <file.html>
    """
    content_snapshot = json.dumps(
        {"resources": RESOURCES, "asset_types": ASSET_TYPE_DESCRIPTIONS},
        ensure_ascii=False,
    )

    resource_sections = ""
    for uri, meta in RESOURCES.items():
        code = uri.replace("tontine://", "")
        resource_sections += f"""
    <div class="section">
      <div class="section-label">Resource: {html.escape(meta['name'])}</div>
      <div class="field-group">
        <label>Title</label>
        <input type="text" data-section="resource" data-code="{html.escape(code)}" data-field="name"
               value="{html.escape(meta['name'], quote=True)}">
      </div>
      <div class="field-group">
        <label>Short description <span class="hint">(one line summary)</span></label>
        <input type="text" data-section="resource" data-code="{html.escape(code)}" data-field="description"
               value="{html.escape(meta['description'], quote=True)}">
      </div>
      <div class="field-group">
        <label>Full content <span class="hint">(this is what the AI reads word for word)</span></label>
        <textarea data-section="resource" data-code="{html.escape(code)}" data-field="content" rows="22">{html.escape(meta['content'])}</textarea>
      </div>
    </div>"""

    asset_sections = ""
    for code, meta in ASSET_TYPE_DESCRIPTIONS.items():
        asset_sections += f"""
    <div class="section">
      <div class="section-label">Asset: {html.escape(code)} — {html.escape(meta['label'])}</div>
      <div class="field-group">
        <label>Display name</label>
        <input type="text" data-section="asset" data-code="{html.escape(code)}" data-field="label"
               value="{html.escape(meta['label'], quote=True)}">
      </div>
      <div class="field-group">
        <label>Risk level label</label>
        <input type="text" data-section="asset" data-code="{html.escape(code)}" data-field="risk"
               value="{html.escape(meta['risk'], quote=True)}">
      </div>
      <div class="field-group">
        <label>Description <span class="hint">(shown to the AI and in the dashboard)</span></label>
        <textarea data-section="asset" data-code="{html.escape(code)}" data-field="description" rows="4">{html.escape(meta['description'])}</textarea>
      </div>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tontine Trust — Content Review</title>
<style>
  :root {{
    --blue: #1a6fc4;
    --blue-dark: #154f8e;
    --blue-light: #e8f1fb;
    --bg: #f5f7fa;
    --surface: #ffffff;
    --border: #d8e3ef;
    --text: #1a2332;
    --muted: #5a6e85;
    --green: #1a7a4a;
    --green-light: #e6f4ed;
    --radius: 8px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 15px; line-height: 1.6; }}

  header {{ background: var(--blue); padding: 20px 40px; display: flex; align-items: center; gap: 14px; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 8px rgba(0,0,0,0.18); }}
  .logo {{ font-size: 22px; font-weight: 700; color: #fff; }}
  .logo span {{ font-weight: 300; opacity: 0.85; }}
  .header-tag {{ background: #fff; color: var(--blue); font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; padding: 3px 9px; border-radius: 4px; }}
  .save-btn-header {{ margin-left: auto; background: #fff; color: var(--blue); border: none; padding: 9px 22px; border-radius: 6px; font-size: 14px; font-weight: 700; cursor: pointer; transition: background 0.15s; }}
  .save-btn-header:hover {{ background: var(--blue-light); }}

  .intro {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 28px 40px; }}
  .intro h2 {{ font-size: 18px; color: var(--blue); margin-bottom: 14px; }}
  .steps {{ list-style: none; counter-reset: step; display: flex; flex-direction: column; gap: 10px; }}
  .steps li {{ counter-increment: step; display: flex; align-items: flex-start; gap: 12px; font-size: 14px; color: var(--muted); }}
  .steps li::before {{ content: counter(step); background: var(--blue); color: #fff; font-size: 12px; font-weight: 700; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px; }}
  .steps li strong {{ color: var(--text); }}

  main {{ max-width: 900px; margin: 0 auto; padding: 32px 40px 60px; }}
  h2.chapter {{ font-size: 16px; font-weight: 700; color: var(--blue); text-transform: uppercase; letter-spacing: 0.8px; margin: 40px 0 16px; padding-bottom: 8px; border-bottom: 2px solid var(--blue-light); }}

  .section {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px 28px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
  .section-label {{ font-size: 13px; font-weight: 700; color: var(--blue-dark); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 18px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}
  .field-group {{ margin-bottom: 16px; }}
  .field-group:last-child {{ margin-bottom: 0; }}
  label {{ display: block; font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 6px; }}
  .hint {{ font-weight: 400; color: var(--muted); font-size: 12px; }}
  input[type="text"] {{ width: 100%; padding: 9px 12px; border: 1px solid var(--border); border-radius: 6px; font-size: 14px; color: var(--text); background: var(--bg); font-family: inherit; transition: border-color 0.15s; }}
  input[type="text"]:focus {{ outline: none; border-color: var(--blue); background: #fff; }}
  textarea {{ width: 100%; padding: 10px 12px; border: 1px solid var(--border); border-radius: 6px; font-size: 13px; color: var(--text); background: var(--bg); font-family: "SF Mono", "Fira Code", monospace; line-height: 1.55; resize: vertical; transition: border-color 0.15s; }}
  textarea:focus {{ outline: none; border-color: var(--blue); background: #fff; }}

  .save-section {{ background: var(--green-light); border: 2px solid var(--green); border-radius: var(--radius); padding: 24px 28px; margin-top: 40px; text-align: center; }}
  .save-section p {{ color: var(--muted); font-size: 14px; margin-bottom: 16px; }}
  .save-btn-big {{ background: var(--green); color: #fff; border: none; padding: 14px 40px; border-radius: 8px; font-size: 16px; font-weight: 700; cursor: pointer; letter-spacing: 0.2px; transition: background 0.15s; }}
  .save-btn-big:hover {{ background: #145c38; }}
  .saved-msg {{ display: none; margin-top: 14px; color: var(--green); font-weight: 600; font-size: 14px; }}
</style>
</head>
<body>

<header>
  <div class="logo">Tontine<span>Trust</span></div>
  <span class="header-tag">Content Review</span>
  <button class="save-btn-header" onclick="saveChanges()">&#8595; Save My Changes</button>
</header>

<div class="intro">
  <h2>How to use this file</h2>
  <ol class="steps">
    <li><strong>Read through the content below.</strong> These are the exact texts the AI uses to answer questions about Tontine Trust.</li>
    <li><strong>Click on any field to edit it.</strong> White boxes are short labels. The larger grey boxes contain the full text the AI reads.</li>
    <li><strong>When you are done, click "Save My Changes"</strong> — either the button at the top right or the large green button at the bottom. A new file will be saved to your Downloads folder.</li>
    <li><strong>Send the downloaded file back</strong> to your developer. They will apply the changes with one command.</li>
  </ol>
</div>

<main>
  <h2 class="chapter">Educational Resources (what the AI reads)</h2>
  {resource_sections}

  <h2 class="chapter">Asset Types</h2>
  {asset_sections}

  <div class="save-section">
    <p>When you are happy with your edits, click below. A file will be downloaded to your computer — send it to your developer.</p>
    <button class="save-btn-big" onclick="saveChanges()">&#128190; Save My Changes</button>
    <div class="saved-msg" id="saved-msg">&#10003; File downloaded! Send it to your developer.</div>
  </div>
</main>

<script id="content-data" type="application/json">
{content_snapshot}
</script>

<script>
function saveChanges() {{
  const data = {{ resources: {{}}, asset_types: {{}} }};

  document.querySelectorAll('[data-section]').forEach(el => {{
    const section = el.dataset.section;
    const code = el.dataset.code;
    const field = el.dataset.field;
    const value = el.value;
    if (section === 'resource') {{
      if (!data.resources[code]) data.resources[code] = {{}};
      data.resources[code][field] = value;
    }} else if (section === 'asset') {{
      if (!data.asset_types[code]) data.asset_types[code] = {{}};
      data.asset_types[code][field] = value;
    }}
  }});

  document.getElementById('content-data').textContent = JSON.stringify(data, null, 2);

  const ts = new Date().toISOString().slice(0, 10);
  const blob = new Blob(['<!DOCTYPE html>' + document.documentElement.outerHTML], {{ type: 'text/html;charset=utf-8' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'tontine_content_' + ts + '.html';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(a.href);

  document.getElementById('saved-msg').style.display = 'block';
}}
</script>

</body>
</html>"""
