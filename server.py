#!/usr/bin/env python3
"""Tontine MCP Server — exposes the Tontinator calculator and educational content to LLMs.

Run modes:
  python3 server.py              # stdio mode (Claude Code CLI / local use)
  python3 server.py --http       # HTTP/SSE mode (claude.ai web via ngrok)
  python3 server.py --http --port 8080

HTTP endpoints (--http mode only):
  /          Dashboard — shows all tools, assets, and resources in a browser
  /editor    Content editor — downloadable HTML for non-technical content review
  /sse       MCP SSE connection (used by claude.ai)
  /messages/ MCP message endpoint (used by claude.ai)
"""

import argparse
import asyncio

import httpx
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from api import build_payload, call_tontinator
from context_data import ASSET_TYPE_DESCRIPTIONS, RESOURCES
from formatting import format_comparison, format_single_result

DEFAULT_ASSET_TYPE = "XAU10Y"

# Maps topic slug → resource URI for the get_tontine_info tool.
# Auto-derived from RESOURCES so adding a resource to content.json requires no code change.
# Example: "tontine://what-is-a-tontine" → key "what_is_a_tontine"
TOPIC_TO_URI: dict[str, str] = {
    uri.replace("tontine://", "").replace("-", "_"): uri
    for uri in RESOURCES
}

app = Server("tontine-mcp")


def text_response(text: str) -> list[types.TextContent]:
    """Wrap a plain string in the MCP TextContent list format all tool handlers must return."""
    return [types.TextContent(type="text", text=text)]


# ---------------------------------------------------------------------------
# MCP Resources — educational documents the AI can read
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
# MCP Tools — actions the AI can call
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
                        "enum": list(TOPIC_TO_URI.keys()) + ["all"],
                        "description": (
                            "Which topic to retrieve: "
                            + ", ".join(
                                f"'{k}' = {RESOURCES[v]['name']}"
                                for k, v in TOPIC_TO_URI.items()
                            )
                            + ". Use 'all' to retrieve everything at once."
                        ),
                        "default": next(iter(TOPIC_TO_URI)),
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
                "IMPORTANT — currency: the Tontinator is currency-agnostic. Contribution amounts "
                "are plain numbers (100,000 is 100,000 regardless of currency). If the user "
                "mentions a currency, accept the amount as-is and explain that returns are "
                "identical across currencies for the same numeric contribution. "
                "IMPORTANT — precision: present results as approximate projections or indicative "
                "ranges, NOT as exact guaranteed amounts. Use language like 'approximately', "
                "'in the range of', or 'projected to be around'. "
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
                        "description": (
                            "One-time lump sum contribution as a plain number (e.g. 500000). "
                            "Currency-agnostic — 500,000 EUR and 500,000 USD produce identical projections."
                        ),
                    },
                    "monthly_amount": {
                        "type": "number",
                        "description": (
                            "Recurring monthly contribution as a plain number "
                            "(optional, can combine with onetime_amount). Currency-agnostic."
                        ),
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
                        "default": DEFAULT_ASSET_TYPE,
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
                                    "description": "Human-readable label for this scenario (e.g. 'Retire at 70')",
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
                                    "default": DEFAULT_ASSET_TYPE,
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
            description=(
                "List available asset allocation types with descriptions. "
                "Call this if the user asks about asset options or before recommending an asset type."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ---------------------------------------------------------------------------
# Tool handlers — one branch per tool name
# ---------------------------------------------------------------------------

def _payload_from_args(args: dict) -> dict:
    """Extract build_payload arguments from a tool arguments dict or scenario dict."""
    return build_payload(
        current_age_years=args["current_age_years"],
        current_age_months=args.get("current_age_months", 0),
        country=args["country"],
        sex=args.get("sex"),
        onetime_amount=args.get("onetime_amount"),
        monthly_amount=args.get("monthly_amount"),
        payout_age_years=args["payout_age_years"],
        payout_age_months=args.get("payout_age_months", 0),
        asset_type=args.get("asset_type", DEFAULT_ASSET_TYPE),
    )


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    if name == "get_tontine_info":
        topic = arguments.get("topic", next(iter(TOPIC_TO_URI)))
        default_uri = next(iter(TOPIC_TO_URI.values()))
        uris = list(TOPIC_TO_URI.values()) if topic == "all" else [TOPIC_TO_URI.get(topic, default_uri)]
        parts = [RESOURCES[uri]["content"] for uri in uris if uri in RESOURCES]
        parts.append(
            "\n---\n"
            "**Educational resources available** (readable via MCP resource protocol):\n"
            + "\n".join(f"- `{uri}` — {RESOURCES[uri]['name']}" for uri in RESOURCES)
            + "\n\nFor precise monthly income numbers, use the `calculate_tontine_payout` tool."
        )
        return text_response("\n\n".join(parts))

    if name == "get_asset_types":
        lines = ["Available asset allocation types:\n"]
        for code, meta in ASSET_TYPE_DESCRIPTIONS.items():
            lines.append(f"  {code} — {meta['label']} ({meta['risk']}): {meta['description']}")
        lines.append(
            "\nNote: asset type affects how contributions grow during the "
            "accumulation phase (before payouts start). It does not affect the "
            "tontine mechanism (mortality credits) itself."
        )
        return text_response("\n".join(lines))

    if name == "calculate_tontine_payout":
        asset_type = arguments.get("asset_type", DEFAULT_ASSET_TYPE)
        async with httpx.AsyncClient() as client:
            result = await call_tontinator(_payload_from_args(arguments), client)
        if isinstance(result, str):
            return text_response(result)
        return text_response(format_single_result(result, asset_type=asset_type))

    if name == "compare_tontine_scenarios":
        scenarios = arguments["scenarios"]
        async with httpx.AsyncClient() as client:
            raw_results = await asyncio.gather(*[
                call_tontinator(_payload_from_args(sc), client)
                for sc in scenarios
            ])
        results_list = [
            (
                sc.get("label", f"Age {sc['current_age_years']}, {sc.get('onetime_amount', 0):,.0f} contributed"),
                {"error": raw} if isinstance(raw, str) else raw,
                sc.get("asset_type", DEFAULT_ASSET_TYPE),
            )
            for sc, raw in zip(scenarios, raw_results)
        ]
        return text_response(format_comparison(results_list))

    return text_response(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# HTTP server (--http mode) — serves MCP over SSE + dashboard pages
# ---------------------------------------------------------------------------

def run_http(port: int) -> None:
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import HTMLResponse, Response
    from starlette.routing import Route

    from views import build_dashboard_html, build_editor_html

    sse = SseServerTransport("/messages/")

    async def handle_dashboard(_request: Request) -> HTMLResponse:
        return HTMLResponse(build_dashboard_html())

    async def handle_editor(_request: Request) -> Response:
        return Response(
            content=build_editor_html(),
            media_type="text/html",
            headers={"Content-Disposition": 'attachment; filename="tontine_content_editor.html"'},
        )

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(request.scope, request.receive, request._send) as (r, w):
            await app.run(r, w, app.create_initialization_options())

    async def handle_messages(request: Request) -> None:
        await sse.handle_post_message(request.scope, request.receive, request._send)

    starlette_app = Starlette(routes=[
        Route("/",         endpoint=handle_dashboard),
        Route("/editor",   endpoint=handle_editor),
        Route("/sse",      endpoint=handle_sse),
        Route("/messages/", endpoint=handle_messages, methods=["POST"]),
    ])

    print(f"Tontine MCP server running on http://0.0.0.0:{port}")
    print(f"  Dashboard:    http://localhost:{port}/")
    print(f"  Editor:       http://localhost:{port}/editor")
    print(f"  SSE endpoint: http://0.0.0.0:{port}/sse")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)


async def run_stdio() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tontine MCP Server")
    parser.add_argument("--http", action="store_true", help="Run as HTTP/SSE server (for claude.ai web via ngrok)")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP mode (default: 8000)")
    args = parser.parse_args()

    if args.http:
        run_http(args.port)
    else:
        asyncio.run(run_stdio())
