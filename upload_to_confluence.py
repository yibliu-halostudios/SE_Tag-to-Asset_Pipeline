"""Upload the HTML report to Confluence via the Atlassian MCP SSE protocol.

Usage:
    python upload_to_confluence.py
    python upload_to_confluence.py --page-id PAGE_ID --title "Custom Title"

Prerequisites:
    pip install requests

The script reads the MCP OAuth token from ~/.mcp-auth/ (auto-populated by
mcp-remote when Copilot CLI connects to the Atlassian MCP server).
"""

import argparse
import glob
import json
import os
import queue
import sys
import threading
import time
import uuid

import requests

# ── Defaults ────────────────────────────────────────────────────────────────
DEFAULT_PAGE_ID = "834469987"  # Tag-to-Asset Pipeline Confluence page
DEFAULT_TITLE = "Tag-to-Asset Pipeline \u2014 Analysis & Recommendations"
DEFAULT_CLOUD_ID = "343industries.atlassian.net"
MCP_SSE_URL = "https://mcp.atlassian.com/v1/sse"
HTML_FILE = os.path.join(os.path.dirname(__file__),
                         "Tag-to-Asset_Pipeline_Recommendations.html")


def find_token():
    """Locate the most recent mcp-remote OAuth token."""
    auth_dir = os.path.join(os.path.expanduser("~"), ".mcp-auth")
    if not os.path.isdir(auth_dir):
        sys.exit(f"ERROR: {auth_dir} not found. Connect Copilot CLI to Atlassian first.")

    token_files = glob.glob(os.path.join(auth_dir, "**", "*_tokens.json"), recursive=True)
    if not token_files:
        sys.exit("ERROR: No OAuth token files found in ~/.mcp-auth/")

    newest = max(token_files, key=os.path.getmtime)
    with open(newest, encoding="utf-8") as f:
        tokens = json.load(f)
    print(f"Using token from: {os.path.relpath(newest, auth_dir)}")
    return tokens["access_token"]


def mcp_connect(access_token):
    """Connect to the MCP SSE endpoint and return (post_url, result_queue)."""
    result_queue = queue.Queue()

    sse_resp = requests.get(
        MCP_SSE_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "text/event-stream"},
        stream=True, timeout=30,
    )
    if sse_resp.status_code != 200:
        sys.exit(f"SSE connect failed: {sse_resp.status_code}")

    post_url = None
    event_type = ""
    lines_iter = sse_resp.iter_lines(decode_unicode=True)
    for line in lines_iter:
        if line and line.startswith("event:"):
            event_type = line[6:].strip()
        elif line and line.startswith("data:") and event_type == "endpoint":
            post_url = "https://mcp.atlassian.com" + line[5:].strip()
            break

    if not post_url:
        sys.exit("ERROR: No POST endpoint received from SSE")

    def reader():
        try:
            for line in lines_iter:
                if line and line.startswith("data:"):
                    try:
                        result_queue.put(json.loads(line[5:].strip()))
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

    threading.Thread(target=reader, daemon=True).start()

    hdrs = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    requests.post(post_url, json={
        "jsonrpc": "2.0", "method": "initialize", "id": 1,
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "upload-script", "version": "1.0"},
        },
    }, headers=hdrs)

    try:
        result_queue.get(timeout=10)
    except queue.Empty:
        sys.exit("ERROR: No response to MCP initialize")

    requests.post(post_url, json={
        "jsonrpc": "2.0", "method": "notifications/initialized"
    }, headers=hdrs)
    time.sleep(0.5)

    return post_url, hdrs, result_queue


def upload(post_url, hdrs, result_queue, html, page_id, title, cloud_id):
    """Send the HTML to Confluence via the macro-html extension."""
    adf = {
        "version": 1,
        "type": "doc",
        "content": [{
            "type": "extension",
            "attrs": {
                "layout": "full-width",
                "extensionType": "com.atlassian.confluence.macro.core",
                "extensionKey": "macro-html",
                "parameters": {
                    "macroParams": {
                        "sourceType": {"value": "MacroBody"},
                        "darkmode": {"value": "auto"},
                        "syntax": {"value": "HTML"},
                        "url": {"value": ""},
                        "__bodyContent": {"value": html},
                    },
                    "macroMetadata": {
                        "macroId": {"value": str(uuid.uuid4())},
                        "schemaVersion": {"value": "1"},
                        "title": "HTML",
                    },
                },
                "localId": str(uuid.uuid4()),
            },
        }],
    }

    adf_str = json.dumps(adf, ensure_ascii=False)
    print(f"HTML: {len(html):,} chars  |  ADF payload: {len(adf_str):,} chars")

    r = requests.post(post_url, json={
        "jsonrpc": "2.0", "method": "tools/call", "id": 2,
        "params": {
            "name": "updateConfluencePage",
            "arguments": {
                "cloudId": cloud_id,
                "pageId": page_id,
                "body": adf_str,
                "contentFormat": "adf",
                "title": title,
            },
        },
    }, headers=hdrs, timeout=60)

    if r.status_code != 202:
        sys.exit(f"POST rejected: {r.status_code} {r.text[:300]}")

    try:
        msg = result_queue.get(timeout=60)
    except queue.Empty:
        sys.exit("ERROR: Timeout waiting for Confluence response")

    if "error" in msg:
        sys.exit(f"ERROR: {json.dumps(msg['error'])[:500]}")

    result = msg.get("result", {})
    if result.get("isError"):
        for c in result.get("content", []):
            print(c.get("text", "")[:500])
        sys.exit("Upload failed (isError=True)")

    for c in result.get("content", []):
        text = c.get("text", "")
        if "version" in text:
            try:
                data = json.loads(text)
                ver = data.get("version", {}).get("number", "?")
                page_url = data.get("links", {}).get("base", "") + data.get("links", {}).get("webui", "")
                print(f"\n\u2713 Page updated to version {ver}")
                print(f"  {page_url}")
            except json.JSONDecodeError:
                print(text[:300])

    return True


def main():
    parser = argparse.ArgumentParser(description="Upload HTML report to Confluence")
    parser.add_argument("--html", default=HTML_FILE, help="Path to HTML file")
    parser.add_argument("--page-id", default=DEFAULT_PAGE_ID, help="Confluence page ID")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Page title")
    parser.add_argument("--cloud-id", default=DEFAULT_CLOUD_ID, help="Atlassian cloud ID")
    args = parser.parse_args()

    if not args.page_id:
        sys.exit("ERROR: --page-id is required. Set DEFAULT_PAGE_ID in the script or pass --page-id.")

    if not os.path.isfile(args.html):
        sys.exit(f"ERROR: HTML file not found: {args.html}")

    with open(args.html, "r", encoding="utf-8") as f:
        html = f.read()

    print(f"File: {os.path.basename(args.html)}  ({len(html):,} chars)")
    print(f"Page: {args.page_id}  Title: {args.title}")
    print()

    access_token = find_token()
    print("Connecting to Atlassian MCP...")
    post_url, hdrs, result_queue = mcp_connect(access_token)
    print("Connected. Uploading...")
    upload(post_url, hdrs, result_queue, html, args.page_id, args.title, args.cloud_id)


if __name__ == "__main__":
    main()
