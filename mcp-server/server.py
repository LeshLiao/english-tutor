"""english-practice MCP Server。

所有工具都呼叫 FastAPI 後端，不直接碰資料庫。
環境變數：
  BACKEND_URL    後端位址，預設 http://localhost:8000
  API_KEY        後端的 X-API-Key；未設定時會讀專案根目錄 .env
  MCP_TRANSPORT  stdio（預設）或 http（Streamable HTTP，步驟 09 才用）
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

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

mcp = MCPServer(
    name="english-practice",
    instructions=(
        "Tools for recording the user's English mistakes. "
        "Always call list_error_types before save_sentence so that error type names are reused "
        "instead of inventing synonyms."
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


if __name__ == "__main__":
    if MCP_TRANSPORT == "http":
        # 步驟 09 再補認證與 host/port 設定
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
