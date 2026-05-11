#!/usr/bin/env python3
"""Tontine MCP Server — wraps api.mytontine.com for LLM tool use."""

import argparse
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

API_BASE = "https://api.mytontine.com"
TONTINATOR_ENDPOINT = f"{API_BASE}/v2/payout_forecast/tontinator"

INVESTMENT_TYPE_DESCRIPTIONS = {
    "BOL": "Bonds / fixed-income (lower risk, steadier returns)",
    "FII": "Real Estate Investment Funds (medium risk, inflation-linked)",
    "VBI": "Variable income / equities (higher risk, higher potential return)",
    "BTC": "Bitcoin / crypto (very high risk, very high potential return)",
}

app = Server("tontine-mcp")


# ---------------------------------------------------------------------------
# Tools declaration
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="calculate_tontine_payout",
            description=(
                "Calculate lifetime income projections using the Tontinator. "
                "Returns monthly payout amounts for a tontine structure vs an annuity, "
                "at key age milestones. "
                "The tontine payout grows over time due to mortality credits — "
                "when pool members die, their balance is redistributed to survivors, "
                "increasing everyone's payout. Use this to give users real numbers "
                "instead of generic estimates."
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
                    "investment_type": {
                        "type": "string",
                        "enum": ["BOL", "FII", "VBI", "BTC"],
                        "description": (
                            "Investment allocation strategy: "
                            "BOL=Bonds, FII=Real Estate Funds, VBI=Variable/Equities, BTC=Bitcoin. "
                            "Affects how contributions grow before payout starts."
                        ),
                        "default": "BOL",
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
                "'what if I invest $300k vs $500k?' or comparing investment types. "
                "Each scenario is a separate calculation request."
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
                                "investment_type": {
                                    "type": "string",
                                    "enum": ["BOL", "FII", "VBI", "BTC"],
                                    "default": "BOL",
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
            name="get_investment_types",
            description="List available investment allocation types with descriptions. Call this if the user asks about investment options or before recommending an investment type.",
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
    investment_type: str,
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
        "contribution_allocations": investment_type or "BOL",
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
    """Returns parsed result dict or an error string."""
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
    """Pick one entry per year at +0, +5, +10, +15, +20 from payout start."""
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


def format_single_result(results: dict, investment_type: str, label: str = "") -> str:
    payouts: list[dict] = results.get("payouts", [])
    currency: str = results.get("currency", "USD")
    total_contributions: float = results.get("_total_contributions", 0)
    annual_inflation: float = results.get("annual_inflation_rate", 0.03)

    if not payouts:
        return "No payout data returned."

    payout_age_years = payouts[0]["age"]["years"]
    milestones = extract_milestones(payouts, payout_age_years)

    header = f"{'=' * 56}\n"
    if label:
        header += f"Scenario: {label}\n"
    header += (
        f"Investment type : {investment_type} — {INVESTMENT_TYPE_DESCRIPTIONS.get(investment_type, '')}\n"
        f"Total invested  : {fmt_currency(total_contributions, currency)}\n"
        f"Inflation rate  : {annual_inflation * 100:.1f}% per year\n"
        f"Payouts start at age {payout_age_years}\n"
        f"{'=' * 56}\n"
    )

    col_age = "Age"
    col_tontine = "Tontine/mo"
    col_tontine_adj = "(inflation adj.)"
    col_annuity = "Annuity/mo"

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

    # Key insight note
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
    """Format multiple scenarios side-by-side summary."""
    parts = []
    for label, results, investment_type in results_list:
        parts.append(format_single_result(results, investment_type, label=label))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    async with httpx.AsyncClient() as client:

        if name == "get_investment_types":
            lines = ["Available investment allocation types:\n"]
            for code, desc in INVESTMENT_TYPE_DESCRIPTIONS.items():
                lines.append(f"  {code}: {desc}")
            lines.append(
                "\nNote: investment type affects how contributions grow during the "
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
                investment_type=arguments.get("investment_type", "BOL"),
            )
            result = await call_tontinator(payload, client)
            if isinstance(result, str):
                return [types.TextContent(type="text", text=result)]

            text = format_single_result(
                result,
                investment_type=arguments.get("investment_type", "BOL"),
            )
            return [types.TextContent(type="text", text=text)]

        if name == "compare_tontine_scenarios":
            scenarios = arguments["scenarios"]
            tasks = []
            for sc in scenarios:
                payload = build_payload(
                    current_age_years=sc["current_age_years"],
                    current_age_months=sc.get("current_age_months", 0),
                    country=sc["country"],
                    sex=sc.get("sex"),
                    onetime_amount=sc.get("onetime_amount"),
                    monthly_amount=sc.get("monthly_amount"),
                    payout_age_years=sc["payout_age_years"],
                    payout_age_months=sc.get("payout_age_months", 0),
                    investment_type=sc.get("investment_type", "BOL"),
                )
                tasks.append(call_tontinator(payload, client))

            raw_results = await asyncio.gather(*tasks)

            results_list = []
            for sc, raw in zip(scenarios, raw_results):
                label = sc.get("label", f"Age {sc['current_age_years']}, ${sc.get('onetime_amount', 0):,.0f}")
                inv = sc.get("investment_type", "BOL")
                if isinstance(raw, str):
                    results_list.append((label, {"error": raw}, inv))
                else:
                    results_list.append((label, raw, inv))

            text = format_comparison(results_list)
            return [types.TextContent(type="text", text=text)]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


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
    from starlette.routing import Route

    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as (r, w):
            await app.run(r, w, app.create_initialization_options())

    async def handle_messages(request: Request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    starlette_app = Starlette(routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages/", endpoint=handle_messages, methods=["POST"]),
    ])

    print(f"Tontine MCP server running on http://0.0.0.0:{port}")
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
