#!/usr/bin/env python3
"""Tontine MCP Server — wraps api.mytontine.com for LLM tool use."""

import argparse
import asyncio
import html
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from context_data import ASSET_TYPE_DESCRIPTIONS, RESOURCES, TOOLS_METADATA

API_BASE = "https://api.mytontine.com"
TONTINATOR_ENDPOINT = f"{API_BASE}/v2/payout_forecast/tontinator"

app = Server("tontine-mcp")


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri=uri,
            name=meta["name"],
            description=meta["description"],
            mimeType=meta["mimeType"],
        )
        for uri, meta in RESOURCES.items()
    ]


@app.read_resource()
async def read_resource(uri: types.AnyUrl) -> str:
    key = str(uri)
    if key not in RESOURCES:
        raise ValueError(f"Unknown resource: {uri}")
    return RESOURCES[key]["content"]


# ---------------------------------------------------------------------------
# Tools declaration
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_tontine_info",
            description=(
                "Get background information about Tontine Trust: what it is, how it compares to annuities, "
                "how mortality credits work, the available asset/distribution profiles, and how "
                "member assets are protected. Call this when the user asks general questions like "
                "'what is a tontine?', 'how does it work?', 'is it safe?', 'is it better than an annuity?', "
                "or 'what asset types are available?'. "
                "Also lists available educational resources for deeper reading."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": ["overview", "vs_annuity", "mortality_credits", "distribution_profiles", "trust_security", "all"],
                        "description": (
                            "Which topic to retrieve: "
                            "'overview' = what is Tontine Trust and how it works, "
                            "'vs_annuity' = tontine vs annuity comparison, "
                            "'mortality_credits' = how payouts grow over time, "
                            "'distribution_profiles' = the asset profiles (Gold Extra/Standard/Reserve, BTC, Bold), "
                            "'trust_security' = how assets are held and protected, "
                            "'all' = everything at once."
                        ),
                        "default": "overview",
                    }
                },
            },
        ),
        types.Tool(
            name="calculate_tontine_payout",
            description=(
                "Calculate illustrative lifetime income projections using the Tontinator. "
                "Returns projected monthly payout figures for a tontine structure vs an annuity "
                "at key age milestones. "
                "The tontine payout grows over time due to mortality credits — "
                "when pool members die, their balance is redistributed to survivors, "
                "increasing everyone's payout. "
                "IMPORTANT: present results as approximate projections or indicative ranges, "
                "NOT as exact guaranteed amounts. Actual payouts will vary based on real asset "
                "performance and actual member mortality. Use language like 'approximately', "
                "'in the range of', 'projected to be around', or 'illustrative figure of'. "
                "If the user is unfamiliar with tontines, call get_tontine_info first."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "current_age_years": {
                        "type": "integer",
                        "description": "Current age in whole years (e.g. 65)",
                    },
                    "current_age_months": {
                        "type": "integer",
                        "description": "Additional months on top of years (0-11, default 0)",
                        "default": 0,
                    },
                    "country": {
                        "type": "string",
                        "description": "Country of residence as ISO 3166-1 alpha-3 code (e.g. USA, GBR, BRA, CAN)",
                    },
                    "sex": {
                        "type": "string",
                        "enum": ["Male", "Female"],
                        "description": "Biological sex — used for actuarial mortality calculations",
                    },
                    "onetime_amount": {
                        "type": "number",
                        "description": "One-time lump sum contribution (e.g. 500000 for $500,000)",
                    },
                    "monthly_amount": {
                        "type": "number",
                        "description": "Recurring monthly contribution amount (optional, can combine with onetime_amount)",
                    },
                    "payout_age_years": {
                        "type": "integer",
                        "description": "Age at which monthly payouts begin (e.g. 70, 75, 84)",
                    },
                    "payout_age_months": {
                        "type": "integer",
                        "description": "Additional months for payout start age (default 0)",
                        "default": 0,
                    },
                    "asset_type": {
                        "type": "string",
                        "enum": ["XAU5Y", "XAU10Y", "XAU20Y", "BTC", "BOL"],
                        "description": (
                            "Asset allocation strategy: "
                            "XAU5Y=Gold Extra (aggressive), XAU10Y=Gold Standard (balanced), "
                            "XAU20Y=Gold Reserved (conservative), BTC=Bitcoin, BOL=Bold (65% gold + 35% BTC). "
                            "Affects how contributions grow before payout starts."
                        ),
                        "default": "XAU10Y",
                    },
                },
                "required": ["current_age_years", "country", "payout_age_years", "onetime_amount"],
            },
        ),
        types.Tool(
            name="compare_tontine_scenarios",
            description=(
                "Compare two or more tontine scenarios side-by-side. "
                "Useful for questions like 'what if I retire at 70 vs 80?' or "
                "'what if I contribute $300k vs $500k?' or comparing asset types. "
                "Each scenario is a separate calculation request. "
                "IMPORTANT: present all figures as approximate projections, not guaranteed amounts. "
                "Use language like 'approximately', 'projected around', or 'in the range of'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scenarios": {
                        "type": "array",
                        "description": "List of scenarios to compare (2-4 recommended)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {
                                    "type": "string",
                                    "description": "Human-readable label for this scenario (e.g. 'Retire at 70', 'Option A')",
                                },
                                "current_age_years": {"type": "integer"},
                                "current_age_months": {"type": "integer", "default": 0},
                                "country": {"type": "string"},
                                "sex": {"type": "string", "enum": ["Male", "Female"]},
                                "onetime_amount": {"type": "number"},
                                "monthly_amount": {"type": "number"},
                                "payout_age_years": {"type": "integer"},
                                "payout_age_months": {"type": "integer", "default": 0},
                                "asset_type": {
                                    "type": "string",
                                    "enum": ["XAU5Y", "XAU10Y", "XAU20Y", "BTC", "BOL"],
                                    "default": "XAU10Y",
                                },
                            },
                            "required": ["current_age_years", "country", "payout_age_years", "onetime_amount"],
                        },
                        "minItems": 2,
                        "maxItems": 4,
                    }
                },
                "required": ["scenarios"],
            },
        ),
        types.Tool(
            name="get_asset_types",
            description="List available asset allocation types with descriptions. Call this if the user asks about asset options or before recommending an asset type.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def build_payload(
    current_age_years: int,
    current_age_months: int,
    country: str,
    sex: str | None,
    onetime_amount: float | None,
    monthly_amount: float | None,
    payout_age_years: int,
    payout_age_months: int,
    asset_type: str,
) -> dict:
    payload: dict = {
        "demographic_data_country_of_residence": country.upper(),
        "demographic_data_current_age": {
            "year": current_age_years,
            "month": current_age_months or 0,
        },
        "contributions": {
            "payout_age": {
                "year": payout_age_years,
                "month": payout_age_months or 0,
            },
        },
        "contribution_allocations": asset_type or "XAU10Y",
        "write_draft_plan": False,
    }
    if sex:
        payload["demographic_data_sex"] = sex
    if onetime_amount:
        payload["contributions"]["onetime_amount"] = int(onetime_amount)
    if monthly_amount:
        payload["contributions"]["monthly_amount"] = int(monthly_amount)
    return payload


async def call_tontinator(payload: dict, client: httpx.AsyncClient) -> dict | str:
    try:
        resp = await client.post(TONTINATOR_ENDPOINT, json=[payload], timeout=30.0)
    except httpx.RequestError as e:
        return f"Network error contacting Tontinator API: {e}"

    if resp.status_code != 200:
        try:
            body = resp.json()
            msg = body.get("message", resp.text)
        except Exception:
            msg = resp.text
        return f"API error {resp.status_code}: {msg}"

    data = resp.json()
    if not data or not isinstance(data, list):
        return "Unexpected API response format."

    item = data[0]
    if "results" not in item:
        return f"API returned no results. Raw: {item}"

    return item["results"]


# ---------------------------------------------------------------------------
# Response formatting
# ---------------------------------------------------------------------------

def extract_milestones(payouts: list[dict], payout_age_years: int) -> list[dict]:
    targets = {payout_age_years + offset for offset in [0, 5, 10, 15, 20]}
    seen: set[int] = set()
    milestones = []
    for p in payouts:
        yr = p["age"]["years"]
        mo = p["age"]["months"]
        if yr in targets and mo == 0 and yr not in seen:
            milestones.append(p)
            seen.add(yr)
    return milestones


def fmt_currency(amount: float | None, currency: str = "USD") -> str:
    if amount is None:
        return "N/A"
    symbol = {"USD": "$", "GBP": "£", "EUR": "€", "BRL": "R$"}.get(currency, currency + " ")
    return f"{symbol}{amount:,.0f}"


def format_single_result(results: dict, asset_type: str, label: str = "") -> str:
    payouts: list[dict] = results.get("payouts", [])
    currency: str = results.get("currency", "USD")
    total_contributions: float = results.get("_total_contributions", 0)
    annual_inflation: float = results.get("annual_inflation_rate", 0.03)

    if not payouts:
        return "No payout data returned."

    payout_age_years = payouts[0]["age"]["years"]
    milestones = extract_milestones(payouts, payout_age_years)

    inv_meta = ASSET_TYPE_DESCRIPTIONS.get(asset_type, {})
    inv_label = inv_meta.get("label", asset_type) if isinstance(inv_meta, dict) else asset_type

    header = f"{'=' * 56}\n"
    header += (
        "NOTE: These are illustrative projections based on current actuarial\n"
        "assumptions and historical asset performance. Present to the user as\n"
        "approximate figures — actual payouts will vary.\n"
        f"{'=' * 56}\n"
    )
    if label:
        header += f"Scenario: {label}\n"
    header += (
        f"Asset type       : {asset_type} — {inv_label}\n"
        f"Total contributed: {fmt_currency(total_contributions, currency)}\n"
        f"Inflation rate   : {annual_inflation * 100:.1f}% per year\n"
        f"Payouts start at age {payout_age_years}\n"
        f"{'=' * 56}\n"
    )

    table_header = f"\n{'Age':<5}  {'Tontine/mo':>12}  {'Infl.adj':>12}  {'Annuity/mo':>12}\n"
    table_header += f"{'-'*5}  {'-'*12}  {'-'*12}  {'-'*12}\n"

    rows = []
    for p in milestones:
        age_yr = p["age"]["years"]
        tontine_amt = p["tontine"].get("amount")
        tontine_adj = p["tontine"].get("amount_inflation_adjusted")
        annuity_amt = p["annuity"].get("amount")
        rows.append(
            f"{age_yr:<5}  {fmt_currency(tontine_amt, currency):>12}  "
            f"{fmt_currency(tontine_adj, currency):>12}  "
            f"{fmt_currency(annuity_amt, currency):>12}"
        )

    first = milestones[0] if milestones else None
    last = milestones[-1] if len(milestones) > 1 else None
    note = ""
    if first and last:
        t_first = first["tontine"].get("amount", 0) or 0
        t_last = last["tontine"].get("amount", 0) or 0
        a_first = first["annuity"].get("amount", 0) or 0
        if t_last > t_first and t_first > 0:
            growth_pct = ((t_last / t_first) - 1) * 100
            note = (
                f"\nKey insight: Tontine payout grows {growth_pct:.0f}% from age "
                f"{first['age']['years']} to {last['age']['years']} due to mortality "
                f"credits — as pool members pass away, their balance is redistributed "
                f"to survivors, increasing everyone's monthly income.\n"
            )
        if a_first and t_first:
            diff = t_first - a_first
            direction = "higher" if diff > 0 else "lower"
            note += (
                f"At payout start, tontine pays {fmt_currency(abs(diff), currency)}/mo "
                f"{direction} than the annuity equivalent.\n"
            )

    return header + table_header + "\n".join(rows) + "\n" + note


def format_comparison(results_list: list[tuple[str, dict, str]]) -> str:
    parts = []
    for label, results, asset_type in results_list:
        parts.append(format_single_result(results, asset_type, label=label))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    async with httpx.AsyncClient() as client:

        if name == "get_tontine_info":
            topic = arguments.get("topic", "overview")
            topic_map = {
                "overview": "tontine://what-is-a-tontine",
                "vs_annuity": "tontine://tontine-vs-annuity",
                "mortality_credits": "tontine://mortality-credits",
                "distribution_profiles": "tontine://distribution-profiles",
                "trust_security": "tontine://trust-property-and-security",
            }
            uris = list(topic_map.values()) if topic == "all" else [topic_map.get(topic, "tontine://what-is-a-tontine")]

            parts = [RESOURCES[uri]["content"] for uri in uris if uri in RESOURCES]
            parts.append(
                "\n---\n"
                "**Educational resources available** (readable via MCP resource protocol):\n"
                + "\n".join(f"- `{uri}` — {RESOURCES[uri]['name']}" for uri in RESOURCES)
                + "\n\nFor precise monthly income numbers, use the `calculate_tontine_payout` tool."
            )
            return [types.TextContent(type="text", text="\n\n".join(parts))]

        if name == "get_asset_types":
            lines = ["Available asset allocation types:\n"]
            for code, meta in ASSET_TYPE_DESCRIPTIONS.items():
                lines.append(f"  {code} — {meta['label']} ({meta['risk']}): {meta['description']}")
            lines.append(
                "\nNote: asset type affects how contributions grow during the "
                "accumulation phase (before payouts start). It does not affect the "
                "tontine mechanism (mortality credits) itself."
            )
            return [types.TextContent(type="text", text="\n".join(lines))]

        if name == "calculate_tontine_payout":
            payload = build_payload(
                current_age_years=arguments["current_age_years"],
                current_age_months=arguments.get("current_age_months", 0),
                country=arguments["country"],
                sex=arguments.get("sex"),
                onetime_amount=arguments.get("onetime_amount"),
                monthly_amount=arguments.get("monthly_amount"),
                payout_age_years=arguments["payout_age_years"],
                payout_age_months=arguments.get("payout_age_months", 0),
                asset_type=arguments.get("asset_type", "XAU10Y"),
            )
            result = await call_tontinator(payload, client)
            if isinstance(result, str):
                return [types.TextContent(type="text", text=result)]
            text = format_single_result(result, asset_type=arguments.get("asset_type", "XAU10Y"))
            return [types.TextContent(type="text", text=text)]

        if name == "compare_tontine_scenarios":
            scenarios = arguments["scenarios"]
            tasks = [
                call_tontinator(
                    build_payload(
                        current_age_years=sc["current_age_years"],
                        current_age_months=sc.get("current_age_months", 0),
                        country=sc["country"],
                        sex=sc.get("sex"),
                        onetime_amount=sc.get("onetime_amount"),
                        monthly_amount=sc.get("monthly_amount"),
                        payout_age_years=sc["payout_age_years"],
                        payout_age_months=sc.get("payout_age_months", 0),
                        asset_type=sc.get("asset_type", "XAU10Y"),
                    ),
                    client,
                )
                for sc in scenarios
            ]
            raw_results = await asyncio.gather(*tasks)

            results_list = []
            for sc, raw in zip(scenarios, raw_results):
                label = sc.get("label", f"Age {sc['current_age_years']}, ${sc.get('onetime_amount', 0):,.0f}")
                inv = sc.get("asset_type", "XAU10Y")
                results_list.append((label, {"error": raw} if isinstance(raw, str) else raw, inv))

            return [types.TextContent(type="text", text=format_comparison(results_list))]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


# ---------------------------------------------------------------------------
# Dashboard HTML (served at / in HTTP mode)
# ---------------------------------------------------------------------------

def build_dashboard_html() -> str:
    risk_badge_color = {
        "Aggressive": "#e05c00",
        "Balanced (default)": "#b8960c",
        "Conservative": "#2a7a4b",
        "Very High Risk / Very High Potential": "#8b1a1a",
        "High Risk / Blended": "#5a3e8a",
    }

    inv_cards = ""
    for code, meta in ASSET_TYPE_DESCRIPTIONS.items():
        badge_color = risk_badge_color.get(meta["risk"], "#555")
        inv_cards += f"""
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
    n_inv = len(ASSET_TYPE_DESCRIPTIONS)

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

  header {{
    background: var(--blue);
    padding: 20px 40px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 2px 8px rgba(26,111,196,0.18);
  }}
  .logo {{ font-size: 24px; font-weight: 700; color: #fff; letter-spacing: -0.3px; }}
  .logo span {{ font-weight: 300; opacity: 0.85; }}
  .tag {{
    background: #fff;
    color: var(--blue);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 4px;
  }}
  .subtitle {{ color: rgba(255,255,255,0.7); font-size: 13px; margin-left: auto; }}

  nav.sections {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 40px;
    display: flex;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }}
  nav.sections a {{
    color: var(--muted);
    text-decoration: none;
    padding: 14px 20px;
    font-size: 13px;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    transition: color 0.15s, border-color 0.15s;
  }}
  nav.sections a:hover {{ color: var(--blue); border-color: var(--blue); }}

  main {{ max-width: 1100px; margin: 0 auto; padding: 40px; }}

  section {{ margin-bottom: 56px; }}
  section h2 {{
    font-size: 18px;
    font-weight: 600;
    color: var(--blue);
    border-bottom: 2px solid var(--blue-mid);
    padding-bottom: 10px;
    margin-bottom: 24px;
  }}

  .intro-box {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--blue);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin-bottom: 32px;
    color: var(--muted);
    font-size: 14px;
    line-height: 1.75;
  }}
  .intro-box strong {{ color: var(--text); }}

  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .card-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }}
  .code-badge {{
    background: var(--blue-light);
    color: var(--blue-dark);
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 13px;
    padding: 2px 10px;
    border-radius: 4px;
    border: 1px solid var(--blue-mid);
    font-weight: 600;
  }}
  .label {{ font-weight: 600; font-size: 15px; color: var(--text); }}
  .risk-badge {{
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    color: #fff;
    letter-spacing: 0.3px;
  }}
  .card p {{ color: var(--muted); font-size: 14px; line-height: 1.65; }}
  .params-line {{ margin-top: 10px; font-size: 13px; color: var(--muted); }}
  .params-label {{ color: var(--blue); font-weight: 600; }}

  .tab-bar {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 20px; }}
  .tab-btn {{
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 7px 15px;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.15s;
  }}
  .tab-btn:hover {{ border-color: var(--blue); color: var(--blue); background: var(--blue-light); }}
  .tab-btn.active {{ background: var(--blue); color: #fff; border-color: var(--blue); font-weight: 600; }}

  .tab-panel {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 28px 32px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .resource-uri {{
    font-family: monospace;
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 20px;
    background: var(--surface2);
    padding: 4px 10px;
    border-radius: 4px;
    display: inline-block;
    border: 1px solid var(--border);
  }}

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

  footer {{
    text-align: center;
    padding: 30px;
    color: var(--muted);
    font-size: 12px;
    border-top: 1px solid var(--border);
    margin-top: 20px;
    background: var(--surface);
  }}
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
      <strong>{n_inv} asset types</strong>, and <strong>{n_resources} educational resources</strong> — markdown documents
      the AI reads to answer questions accurately. All calculation data is powered live by
      <strong>api.mytontine.com</strong>.
    </div>
  </section>

  <section id="tools">
    <h2>Exposed Tools ({n_tools})</h2>
    {tool_cards}
  </section>

  <section id="assets">
    <h2>Asset Types ({n_inv})</h2>
    {inv_cards}
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def run_stdio():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def run_http(port: int):
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import HTMLResponse
    from starlette.routing import Route

    sse = SseServerTransport("/messages/")

    async def handle_dashboard(_request: Request):
        return HTMLResponse(build_dashboard_html())

    async def handle_sse(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as (r, w):
            await app.run(r, w, app.create_initialization_options())

    async def handle_messages(request: Request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    starlette_app = Starlette(routes=[
        Route("/", endpoint=handle_dashboard),
        Route("/sse", endpoint=handle_sse),
        Route("/messages/", endpoint=handle_messages, methods=["POST"]),
    ])

    print(f"Tontine MCP server running on http://0.0.0.0:{port}")
    print(f"Dashboard:    http://localhost:{port}/")
    print(f"SSE endpoint: http://0.0.0.0:{port}/sse")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tontine MCP Server")
    parser.add_argument("--http", action="store_true", help="Run as HTTP/SSE server (for claude.ai web)")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP mode (default: 8000)")
    args = parser.parse_args()

    if args.http:
        run_http(args.port)
    else:
        asyncio.run(run_stdio())
