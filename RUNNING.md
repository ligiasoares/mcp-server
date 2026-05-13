# Running the Tontine MCP Server

---

## Setup (first time only)

Install all dependencies:
```bash
pip install -r requirements.txt
```

---

## Part 1 — Local use with Claude Code CLI (stdio mode)

This mode is for using the MCP server directly inside Claude Code on your machine. No ngrok needed.

The server is already registered in `~/.claude/mcp.json`. Just open Claude Code and the tools are available automatically.

To verify it's running, start a conversation in Claude Code and ask:
> *"What tontine tools do you have available?"*

Claude will list the tools from this MCP server.

---

## Part 2 — Expose to claude.ai via ngrok (HTTP mode)

This mode makes the server accessible from your claude.ai account in the browser.

**Step 1 — Start the MCP server**
```bash
python3 "/home/mr-rolim/Desktop/MCP Tontine/server.py" --http --port 8000
```
Leave this terminal open.

**Step 2 — Start ngrok in a second terminal**
```bash
ngrok http 8000
```
You'll see a line like:
```
Forwarding  https://atrium-crimp-guidance.ngrok-free.app -> http://localhost:8000
```
Copy that `https://...ngrok-free.app` URL. Leave this terminal open too.

**Step 3 — Add the connector on claude.ai**
1. Go to [claude.ai](https://claude.ai) → click your profile → **Settings** → **Connectors**
2. Click **Add custom connector**
3. Name: `Tontinator`
4. URL: paste the ngrok URL and add `/sse` at the end
   - Example: `https://atrium-crimp-guidance.ngrok-free.app/sse`
5. Save

**Step 4 — Test it**
Start a new conversation on claude.ai and ask:
> *"I'm 65, male, USA, $500k contribution. What would my tontine payout be starting at age 80 with Gold Standard?"*

Claude will call the MCP tool automatically and return projected figures.

---

**If the connection drops** — ngrok disconnects when the terminal closes or the free session expires (typically ~2 hours).

To reconnect:
1. Run `ngrok http 8000` again in a terminal
2. Copy the new `https://...ngrok-free.app` URL
3. Go to claude.ai → Settings → Connectors → edit the Tontinator connector
4. Replace the URL (keep the `/sse` suffix)
5. Save — the connection resumes immediately

---

## Part 3 — View the knowledge base dashboard

The dashboard shows everything the AI knows: tools, asset types, and all educational content.

**While the server is running in `--http` mode**, open:
```
http://localhost:8000/
```

> During a demo, the ngrok URL also serves the dashboard publicly at `https://your-ngrok-url.ngrok-free.app/` — no extra setup needed.

---

## Part 4 — Content editor (reviewing / updating AI context)

The content editor lets a non-technical person review and edit the text the AI uses to answer questions about Tontine Trust.

**Step 1 — Download the editor**

While the server is running, go to:
```
http://localhost:8000/editor
```
This downloads `tontine_content_editor.html` automatically.

**Step 2 — Send to your boss**

Email the downloaded file. Your boss opens it by double-clicking — no software needed, just a browser.

**Step 3 — Boss edits and saves**

All fields are editable directly on screen. When done, they click **Save My Changes**. A timestamped file (e.g. `tontine_content_2026-05-13.html`) is downloaded to their computer. They email it back.

**Step 4 — Apply the changes**

Run this command with the file they sent back:
```bash
python3 apply_changes.py tontine_content_2026-05-13.html
```
The script prints exactly which fields changed and updates `content.json`. Then restart the server to apply:
```bash
python3 "/home/mr-rolim/Desktop/MCP Tontine/server.py" --http --port 8000
```
