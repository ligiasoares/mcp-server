# Running the Tontine MCP Server

---

## Part 1 — Expose to claude.ai via ngrok

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
Start a new conversation on claude.ai and ask something like:
> *"I'm 65, male, USA, $500k lump sum. What would my tontine payout be starting at age 80 with Gold Standard?"*

Claude will call the MCP tool automatically and return real numbers.

---

**If it stops working** — ngrok disconnects if the terminal closes or the session expires.
Just run `ngrok http 8000` again, copy the new URL, and update the connector on claude.ai.

---

## Part 2 — View the knowledge base dashboard

The dashboard shows everything the AI knows: tools, investment options, and all educational content.

**While the server is running** (`--http` mode), open your browser:
```
http://localhost:8000/
```

That's it. No extra setup needed — it's served by the same process as the MCP server.

> The dashboard is only available locally. The ngrok URL also serves it publicly at `https://your-ngrok-url.ngrok-free.app/` if you want to show it to someone else during a demo.
