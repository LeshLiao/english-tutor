"""english-practice MCP Server。

所有工具都呼叫 FastAPI 後端，不直接碰資料庫。
環境變數：
  BACKEND_URL    後端位址，預設 http://localhost:8000
  API_KEY        後端的 X-API-Key；未設定時會讀專案根目錄 .env。
                 http 模式下，client 連 MCP 也要帶同一把 key（X-API-Key 或 Authorization: Bearer）
  MCP_TRANSPORT  stdio（預設）或 http（Streamable HTTP，跑在容器裡）
  MCP_HOST / MCP_PORT  http 模式的監聽位址，預設 0.0.0.0:8001
"""

from __future__ import annotations

import hmac
import os
from pathlib import Path
from typing import Literal

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv_fallback() -> None:
    """只在環境變數沒給 API_KEY 時，從專案根目錄 .env 補上（不引入第三方套件）。"""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv_fallback()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.environ.get("API_KEY", "")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8001"))

mcp = MCPServer(
    name="english-practice",
    instructions=(
        "Tools for recording and reviewing the user's English mistakes. "
        "Always call list_error_types before save_sentence so that error type names are reused "
        "instead of inventing synonyms. Use get_error_stats for 'what do I get wrong most', "
        "search_sentences / get_recent_mistakes to review past sentences, and dismiss_sentence "
        "when the user says a recorded sentence was a false positive."
    ),
)

client = httpx.Client(base_url=BACKEND_URL, headers={"X-API-Key": API_KEY}, timeout=10.0)


def _request(method: str, path: str, **kwargs):
    """共用的後端呼叫；把連線失敗與非 2xx 轉成清楚的 ToolError。"""
    try:
        resp = client.request(method, path, **kwargs)
    except httpx.ConnectError as exc:
        raise ToolError(
            f"Cannot reach backend at {BACKEND_URL}. Is `docker compose up -d` running? ({exc})"
        ) from exc
    except httpx.TimeoutException as exc:
        raise ToolError(f"Backend at {BACKEND_URL} timed out: {exc}") from exc
    if resp.status_code == 401:
        raise ToolError("Backend rejected API key (401). Check API_KEY matches backend .env.")
    if resp.is_error:
        raise ToolError(f"Backend returned {resp.status_code} for {method} {path}: {resp.text[:500]}")
    return resp.json()


class ErrorItem(BaseModel):
    error_type: str = Field(
        description=(
            "Error category name, lowercase, short, singular (e.g. 'tense', 'article', 'preposition', "
            "'word choice'). Prefer an existing name from list_error_types."
        )
    )
    error_snippet: str = Field(description="The exact wrong fragment from the original sentence.")
    suggestion: str = Field(description="What the fragment should be instead.")
    description: str | None = Field(
        default=None,
        description="Only used when this creates a brand-new error type: one-line description of the category.",
    )


@mcp.tool()
def list_error_types() -> list[dict]:
    """List all existing error type categories (name + description).

    Call this FIRST before classifying errors, and reuse these names in save_sentence
    so that 'tense' and 'verb tense' do not become two separate categories.
    Returns an empty list when nothing has been recorded yet.
    """
    return [
        {"name": t["name"], "description": t.get("description")}
        for t in _request("GET", "/error-types")
    ]


@mcp.tool()
def save_sentence(
    original_text: str,
    corrected_text: str,
    explanation: str,
    source: Literal["hook", "skill"],
    errors: list[ErrorItem],
) -> dict:
    """Save one checked English sentence together with its classified errors.

    Args:
        original_text: The sentence exactly as the user wrote it.
        corrected_text: The fully corrected sentence. Same as original_text if it was already correct.
        explanation: Short explanation of why the corrections were needed (may be empty if no errors).
        source: 'skill' when invoked via /english-check, 'hook' when triggered automatically.
        errors: One item per mistake. Use an empty list for a correct sentence.
                error_type names not yet in list_error_types are created automatically.

    Returns the new sentence id and the error types actually used (including any newly created).
    """
    payload = {
        "original_text": original_text,
        "corrected_text": corrected_text,
        "explanation": explanation,
        "source": source,
        "errors": [e.model_dump() for e in errors],
    }
    data = _request("POST", "/sentences", json=payload)
    return {
        "sentence_id": data["id"],
        "created_at": data["created_at"],
        "error_types_used": sorted({e["error_type"]["name"] for e in data["errors"]}),
        "error_count": len(data["errors"]),
    }


def _summarize(sentence: dict) -> dict:
    """把後端的句子 JSON 精簡成 Claude 好讀的形狀。"""
    return {
        "id": sentence["id"],
        "created_at": sentence["created_at"],
        "source": sentence["source"],
        "original_text": sentence["original_text"],
        "corrected_text": sentence["corrected_text"],
        "explanation": sentence["explanation"],
        "is_dismissed": sentence["is_dismissed"],
        "errors": [
            {
                "error_type": e["error_type"]["name"],
                "error_snippet": e["error_snippet"],
                "suggestion": e["suggestion"],
            }
            for e in sentence["errors"]
        ],
    }


@mcp.tool()
def get_error_stats(from_date: str | None = None, to_date: str | None = None) -> list[dict]:
    """Count how many times each error type occurred, most frequent first.

    Dismissed (false-positive) sentences are excluded. Use this to answer
    "what mistakes do I make most often?".

    Args:
        from_date: Optional ISO date/datetime (e.g. '2026-10-01'); only count sentences saved on or after it.
        to_date: Optional ISO date/datetime; only count sentences saved on or before it.

    Returns a list of {error_type, count}, empty when nothing has been recorded.
    """
    params = {k: v for k, v in (("from", from_date), ("to", to_date)) if v}
    return [
        {"error_type": row["error_type"], "count": row["count"]}
        for row in _request("GET", "/stats/errors", params=params)
    ]


@mcp.tool()
def search_sentences(
    error_type: str | None = None,
    keyword: str | None = None,
    limit: int = 20,
    include_dismissed: bool = False,
) -> list[dict]:
    """Search previously saved sentences for review, newest first.

    Args:
        error_type: Only sentences containing this error type (use a name from list_error_types).
        keyword: Case-insensitive substring matched against the original and corrected text.
        limit: Maximum number of sentences to return (1-100).
        include_dismissed: Also return sentences marked as false positives.

    Returns each sentence with its id, texts, explanation and the list of errors.
    """
    params: dict = {"limit": max(1, min(limit, 100)), "include_dismissed": include_dismissed}
    if error_type:
        params["error_type"] = error_type
    if keyword:
        params["q"] = keyword
    return [_summarize(s) for s in _request("GET", "/sentences", params=params)]


@mcp.tool()
def get_recent_mistakes(limit: int = 10) -> list[dict]:
    """Return the user's most recent sentences that contained at least one error, newest first.

    Call this before checking a new sentence so you can point out when the user repeats
    a mistake they made recently (e.g. "this is the 3rd tense error this week").

    Args:
        limit: Maximum number of sentences to return (1-50).

    Returns the same shape as search_sentences; correct sentences and dismissed ones are skipped.
    """
    limit = max(1, min(limit, 50))
    # 後端沒有「只要有錯的句子」篩選，多抓一些再在本地過濾
    rows = _request("GET", "/sentences", params={"limit": min(limit * 3, 500)})
    return [_summarize(s) for s in rows if s["errors"]][:limit]


@mcp.tool()
def dismiss_sentence(sentence_id: int, dismissed: bool = True) -> dict:
    """Mark a saved sentence as a false positive so it no longer counts in statistics or reviews.

    Args:
        sentence_id: The id returned by save_sentence or shown in search results.
        dismissed: True to dismiss (default); False to undo a previous dismissal.

    Returns the sentence id and its new is_dismissed value.
    """
    data = _request("PATCH", f"/sentences/{sentence_id}", json={"is_dismissed": dismissed})
    return {"sentence_id": data["id"], "is_dismissed": data["is_dismissed"]}


# ---------------------------------------------------------------------------
# HTTP 模式（Streamable HTTP）：API key 認證 + 健康檢查
# ---------------------------------------------------------------------------


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health(_: Request) -> Response:
    """給 docker compose healthcheck 用，不需要認證。"""
    return JSONResponse({"status": "ok", "transport": "http"})


def _presented_key(scope: Scope) -> str | None:
    headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
    if "x-api-key" in headers:
        return headers["x-api-key"].strip()
    auth = headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


class ApiKeyMiddleware:
    """純 ASGI middleware：除了 /health 之外，每個請求都要帶正確的 API key，否則 401。"""

    def __init__(self, app: ASGIApp, api_key: str, exempt_paths: tuple[str, ...] = ("/health",)) -> None:
        self.app = app
        self.api_key = api_key
        self.exempt_paths = exempt_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in self.exempt_paths:
            await self.app(scope, receive, send)
            return
        presented = _presented_key(scope)
        if presented is None or not hmac.compare_digest(presented, self.api_key):
            response = PlainTextResponse("Unauthorized: missing or invalid API key", status_code=401)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


def build_http_app():
    if not API_KEY:
        raise SystemExit("API_KEY is required in http mode (refusing to start an unauthenticated MCP server)")
    # stateless + json_response：每個請求獨立、不在記憶體存 session，之後可水平擴展
    app = mcp.streamable_http_app(
        streamable_http_path="/mcp", stateless_http=True, json_response=True, host=MCP_HOST
    )
    app.add_middleware(ApiKeyMiddleware, api_key=API_KEY)
    return app


if __name__ == "__main__":
    if MCP_TRANSPORT == "http":
        import uvicorn

        uvicorn.run(build_http_app(), host=MCP_HOST, port=MCP_PORT, log_level="info")
    else:
        mcp.run(transport="stdio")
