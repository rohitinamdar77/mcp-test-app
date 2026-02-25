# 🏨 StayBot – Hotel Booking MCP Server

A **Booking.com-style hotel search and booking MCP server** built with Python + FastAPI,
deployable on [Railway](https://railway.app) and connectable directly to **ChatGPT**.

---

## 🛠 3 MCP Tools

| Tool | Description |
|------|-------------|
| `search_hotels` | Search hotels by city, dates, guests, price & rating |
| `get_hotel_details` | Full hotel info: rooms, amenities, address, pricing |
| `create_booking` | Book a room and get a confirmation ID instantly |

---

## 🚀 Deploy to Railway (5 minutes)

### Option A – GitHub (recommended)

1. Push this folder to a GitHub repo
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Select your repo → Railway auto-detects Python and deploys
4. Go to **Settings → Domains** → click **Generate Domain**
5. Your MCP URL is: `https://your-app.up.railway.app/mcp`

### Option B – Railway CLI

```bash
npm install -g @railway/cli
railway login
railway init
railway up
railway domain
```

---

## 🤖 Connect to ChatGPT

1. Open [chatgpt.com](https://chatgpt.com)
2. Click the **"+"** icon → **"Add MCP Server"**
3. Enter your Railway URL:
   ```
   https://your-app.up.railway.app/mcp
   ```
4. Click **Connect** — ChatGPT will discover all 3 tools automatically ✅

### Example prompts to try in ChatGPT:
- *"Find hotels in Paris for 2 nights, June 15–17, 2 guests under $400/night"*
- *"Show me full details for htl_001"*
- *"Book the Deluxe Suite at The Grand Plaza for John Smith, john@example.com"*

---

## 🧪 Local Development

```bash
pip install -r requirements.txt
python main.py
```

Then open:
- **Connect screen**: http://localhost:8000/
- **MCP endpoint**: http://localhost:8000/mcp
- **Health check**: http://localhost:8000/health
- **REST API**: http://localhost:8000/api/hotels?city=paris

### Test with curl:

```bash
# List tools
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# Search hotels
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_hotels","arguments":{"city":"paris","guests":2}}}'

# Get hotel details
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_hotel_details","arguments":{"hotel_id":"htl_001"}}}'
```

---

## 📁 Project Structure

```
booking-mcp/
├── main.py           # FastAPI MCP server (all-in-one)
├── requirements.txt  # Python dependencies
├── Procfile          # Railway start command
├── railway.json      # Railway config
└── README.md
```

---

## 🏗 Architecture

```
ChatGPT ──► POST /mcp  ──► JSON-RPC 2.0 handler
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
             search_hotels  get_hotel  create_booking
                           _details
```

MCP transport: **Streamable HTTP** (JSON-RPC 2.0 over POST)
No auth required for this POC.
