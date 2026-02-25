# Hotel MCP Server (ChatGPT App Compatible)

This is a sample MCP (Model Context Protocol) server you can deploy on Railway and connect to ChatGPT Apps.

## Features

- Hotel search tool
- Mock data (replace with real API)
- Booking.com-style widget UI
- Railway-ready deployment

## Deploy to Railway

1. Push this repo to GitHub
2. Go to Railway
3. New Project → Deploy from GitHub
4. Done

Your MCP endpoint:

https://your-app.up.railway.app/mcp

## Local Run

pip install -r requirements.txt
uvicorn server:app --reload --port 8000

Open:

http://localhost:8000/mcp