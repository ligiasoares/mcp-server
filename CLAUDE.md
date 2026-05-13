# Tontine MCP Server — Project Context

This file gives an AI assistant (or new developer) everything needed to understand and work on this codebase without prior context.

---

## What this project does

This is a **Model Context Protocol (MCP) server** that exposes the [Tontine Trust](https://tontine.com) Tontinator calculator to AI assistants like Claude.

Instead of giving vague generic answers about retirement income, Claude can call this server's tools to get real projected payout figures from `api.mytontine.com` and read accurate educational content about how Tontine Trust works.

**MCP** is Anthropic's open standard for connecting AI assistants to external tools and knowledge. The server speaks the MCP protocol over:
- **stdio** — for Claude Code CLI (local use)
- **HTTP/SSE** — for claude.ai web (requires ngrok to expose localhost)

---

## File map

```
server.py          Main entry point. MCP tool declarations, tool handlers,
                   HTTP routing. Everything the AI protocol touches lives here.

api.py             Tontinator API client. build_payload() constructs the request,
                   call_tontinator() sends it and returns results or an error string.

formatting.py      Turns raw API results into readable text blocks for the LLM.
                   extract_milestones(), fmt_amount(), format_single_result(),
                   format_comparison(), _build_insight_note().

views.py           HTML page builders. build_dashboard_html() for the /  page,
                   build_editor_html() for the /editor download.

context_data.py    Loads content.json at import time and exposes RESOURCES,
                   ASSET_TYPE_DESCRIPTIONS, and TOOLS_METADATA to the rest of the app.

content.json       Source of truth for all editable content: the 5 educational
                   resources (markdown) and 5 asset type descriptions. Edit this
                   file (or use the editor workflow) to change what the AI knows.

apply_changes.py   CLI script. Takes the HTML file the boss downloads from /editor,
                   extracts their edits, and merges them into content.json.

requirements.txt   Python dependencies: mcp, httpx, starlette, uvicorn.

RUNNING.md         Step-by-step instructions for running the server, ngrok setup,
                   the dashboard, and the content editor workflow.

.gitignore         Excludes __pycache__ and common editor/OS noise.
```

---

## How to run

See [RUNNING.md](RUNNING.md) for full instructions. Short version:

```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Local use (Claude Code CLI)
python3 server.py

# Web use (claude.ai via ngrok) — then visit http://localhost:8000/
python3 server.py --http --port 8000
```

---

## Architecture notes

### Content is data, not code

All text the AI reads — resource documents, asset descriptions — lives in `content.json`, not in Python source. The flow is:

```
content.json → context_data.py → RESOURCES / ASSET_TYPE_DESCRIPTIONS
                                        ↓
                          server.py (MCP tools + resources)
                          formatting.py (result text)
                          views.py (HTML pages)
```

To change what the AI knows, edit `content.json` (or use the `/editor` → `apply_changes.py` workflow) and restart the server. No Python changes needed.

### Topic map is auto-derived

`TOPIC_TO_URI` in `server.py` is built automatically from `RESOURCES` keys at startup. Adding a new resource to `content.json` makes it instantly available as a topic in `get_tontine_info` — no code change required.

### HTTP client scope

`httpx.AsyncClient` is only opened inside the tool handler branches that make API calls (`calculate_tontine_payout`, `compare_tontine_scenarios`). Tools that only read local data (`get_tontine_info`, `get_asset_types`) never open an HTTP connection.

---

## Key constraints — read before making changes

### Language
- Never use the words **"investment"**, **"investments"**, **"deposit"**, or **"deposits"** anywhere in tool descriptions, resource content, or output. The correct terms are **"contribution"** (money going in) and **"asset"** (the allocation type).
- Run `grep -ri "invest\|deposit" *.py content.json` before committing to verify.

### Figures are approximate
- The Tontinator returns point estimates. The AI must present results as **approximate projections**, not guaranteed amounts.
- The `format_single_result()` output block includes a NOTE header reminding the AI of this. Tool descriptions also carry `IMPORTANT` instructions on precision and language.

### Currency-agnostic
- The Tontinator API is **currency-agnostic** — 100,000 EUR and 100,000 USD produce identical results. No currency symbols are added to output figures.
- `fmt_amount()` in `formatting.py` formats numbers without any symbol. Do not add currency logic.

### Favourable tone toward Tontine Trust
- All educational content (resources in `content.json`) should present Tontine Trust accurately and favourably. Caveats (e.g. "not suitable if you need liquidity") are fine and expected — but the overall framing should be positive.

### Default asset type
- `DEFAULT_ASSET_TYPE = "XAU10Y"` (Gold Standard) is defined once at the top of `server.py`. Change it there only.

---

## The Tontinator API

- **Endpoint**: `POST https://api.mytontine.com/v2/payout_forecast/tontinator`
- **Auth**: none required
- **Request**: JSON array containing one payload object (see `build_payload()` in `api.py`)
- **Response**: JSON array; `data[0]["results"]` contains `payouts[]`, `_total_contributions`, `annual_inflation_rate`
- Each payout entry has `age`, `tontine.amount`, `tontine.amount_inflation_adjusted`, `annuity.amount`
- The server shows milestones at payout start age +0, +5, +10, +15, +20 years

---

## Content editor workflow (for non-technical reviewers)

1. Run server in `--http` mode
2. Visit `http://localhost:8000/editor` — downloads `tontine_content_editor.html`
3. Send file to reviewer; they open it, edit in browser, click **Save My Changes**
4. They email back the timestamped HTML file
5. Developer runs: `python3 apply_changes.py tontine_content_YYYY-MM-DD.html`
6. Restart the server
