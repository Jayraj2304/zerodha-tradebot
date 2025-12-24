# Video Script: ZERODHA TRADEBOT - AI-Powered Trading Assistant

---

## 🎬 SLIDE 1: INTRO (0:00 - 0:30)

> *"Hello everyone, and welcome to this video walkthrough. Today, I'll be presenting my project: the **ZERODHA TRADEBOT** – an AI-Powered Trading Assistant."*
>
> *"The goal of this project is to build a **back-end system** that connects **Zerodha's Kite Connect APIs** with an **AI agent** using the **Model Context Protocol (MCP)**. This allows users to interact with their trading portfolio using **natural language** through Claude AI."*

---

## 📊 SLIDE 2: THE PROBLEM (0:30 - 1:15)

> *"Let me first explain the problem we are solving."*
>
> *"Trading platforms like Zerodha Kite provide powerful APIs, but using them typically requires writing code or navigating complex interfaces. What if you could simply **ask in English**: 'What's my portfolio today?' or 'Buy 10 shares of Reliance at 2500'?"*
>
> *"The challenge is: **How do we bridge the gap between human language and trading APIs?**"*
>
> *"The answer is the **Model Context Protocol (MCP)** – a standard that allows AI agents like Claude to access external tools and services securely."*

---

## 🔧 SLIDE 3: THE SOLUTION - MCP SERVER (1:15 - 2:15)

> *"This is where the MCP Server comes in."*
>
> *"We create an **MCP Server in Python** that exposes all the Kite Connect trading functionality as **tools**. These tools can be called by Claude AI to perform real operations."*
>
> *"The architecture is simple but powerful:*
> 1. *User asks Claude a question in natural language.*
> 2. *Claude identifies which tool to use and calls our MCP server.*
> 3. *The MCP server executes the Kite API and returns the response.*
> 4. *Claude formats the response in a human-readable way."*

---

## 🛠️ SLIDE 4: AVAILABLE TOOLS (2:15 - 3:30)

> *"Let me walk you through the tools we've exposed."*

**Show the tool list on screen:**

| Category | Tools | Description |
|----------|-------|-------------|
| **Authentication** | `get_login_url`, `generate_access_token`, `set_access_token` | Handle Kite login flow |
| **Portfolio** | `get_holdings`, `get_positions`, `get_profile` | View your investments |
| **Market Data** | `get_quote`, `get_ltp` | Real-time stock prices |
| **Trading** | `buy_stock`, `sell_stock`, `cancel_order` | Execute trades |
| **Account** | `get_margins`, `get_orders`, `get_order_history` | Account & order info |
| **Utility** | `get_market_status` | Check if market is open |

> *"That's **15 tools** covering the complete trading workflow – from login to order execution."*

---

## 💻 SLIDE 5: CODE WALKTHROUGH - SETUP (3:30 - 4:30)

> *"Now let's walk through the Python code step-by-step."*

**(Show `trading_bot.py` on screen)**

### 1. Imports & Configuration

> *"First, we import the required libraries. We use `kiteconnect` for Zerodha's API, `mcp.server` for the MCP protocol, and `asyncio` for asynchronous operations."*

```python
import os
import json
import asyncio
from datetime import datetime
from typing import Any, Optional
from dotenv import load_dotenv

from kiteconnect import KiteConnect
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Load environment variables
load_dotenv()

# Configuration
KITE_API_KEY = os.getenv("KITE_API_KEY", "your_api_key")
KITE_API_SECRET = os.getenv("KITE_API_SECRET", "your_secret")

# Initialize Kite Connect
kc = KiteConnect(api_key=KITE_API_KEY)
access_token: Optional[str] = None

# Initialize MCP Server
server = Server("trading-bot")
```

> *"Notice how we use environment variables for API keys – this is a security best practice."*

---

## 💻 SLIDE 6: CODE WALKTHROUGH - HELPER FUNCTIONS (4:30 - 5:30)

### 2. Market Hours Detection

> *"We have helper functions like `is_market_open()` that checks if NSE is currently trading. This is important because we need to use AMO (After Market Orders) when the market is closed."*

```python
def is_market_open() -> bool:
    """Check if NSE market is currently open."""
    now = datetime.now()
    
    # Weekend check (Saturday=5, Sunday=6)
    if now.weekday() >= 5:
        return False
    
    # Market hours: 9:15 AM to 3:30 PM IST
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_open <= now <= market_close


def get_order_variety() -> str:
    """Get appropriate order variety based on market hours."""
    return "regular" if is_market_open() else "amo"


def format_response(data: dict) -> str:
    """Format response data as JSON string."""
    return json.dumps(data, indent=2, default=str)
```

> *"The `get_order_variety()` function automatically returns 'amo' for After Market Orders when the market is closed. This saves the user from having to know this technical detail."*

---

## 💻 SLIDE 7: CODE WALKTHROUGH - TOOL DEFINITIONS (5:30 - 7:00)

### 3. Defining Tools for AI

> *"The `list_tools()` function returns all available tools with their names, descriptions, and input schemas. This tells Claude what actions it can perform."*

```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available trading tools exposed to the AI agent."""
    return [
        Tool(
            name="get_login_url",
            description="Generate the Zerodha Kite login URL to authenticate",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="buy_stock",
            description="Place a buy order for a stock. Uses regular order during market hours, AMO otherwise.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Trading symbol (e.g., HDFCBANK)"},
                    "quantity": {"type": "integer", "description": "Number of shares to buy"},
                    "price": {"type": "number", "description": "Limit price per share"},
                    "product": {"type": "string", "enum": ["CNC", "MIS"], "default": "CNC"}
                },
                "required": ["symbol", "quantity", "price"]
            }
        ),
        # ... 13 more tools defined similarly
    ]
```

> *"Each tool has a name, description, and inputSchema. The schema uses JSON Schema format to define what parameters the tool accepts. Claude reads this to understand how to call each tool."*

---

## 💻 SLIDE 8: CODE WALKTHROUGH - TOOL EXECUTION (7:00 - 9:00)

### 4. Executing Tools - The Core Logic

> *"The `call_tool()` function is the heart of the system. When Claude calls a tool, this function routes to the correct Kite API and returns the result."*

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from the AI agent."""
    global access_token
    
    try:
        # AUTHENTICATION TOOLS
        if name == "get_login_url":
            login_url = kc.login_url()
            return [TextContent(
                type="text",
                text=format_response({
                    "success": True,
                    "login_url": login_url,
                    "instructions": [
                        "1. Open this URL in your browser",
                        "2. Login with your Zerodha credentials",
                        "3. After login, copy the 'request_token' from redirect URL",
                        "4. Use 'generate_access_token' tool with this token"
                    ]
                })
            )]
        
        elif name == "generate_access_token":
            request_token = arguments.get("request_token")
            session = kc.generate_session(request_token, api_secret=KITE_API_SECRET)
            access_token = session["access_token"]
            kc.set_access_token(access_token)
            
            return [TextContent(
                type="text",
                text=format_response({
                    "success": True,
                    "access_token": access_token,
                    "message": "Access token generated successfully!"
                })
            )]
```

> *"The function uses a simple if-elif structure to route each tool call. Each branch calls the corresponding Kite Connect API method."*

---

## � SLIDE 9: CODE WALKTHROUGH - PORTFOLIO & TRADING (9:00 - 10:30)

### 5. Portfolio Analysis

> *"When getting holdings, we don't just return raw data – we calculate a summary with total investment, current value, and P&L."*

```python
elif name == "get_holdings":
    holdings = kc.holdings()
    
    # Calculate portfolio summary
    total_investment = sum(h.get("quantity", 0) * h.get("average_price", 0) for h in holdings)
    total_current = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in holdings)
    total_pnl = sum(h.get("pnl", 0) for h in holdings)
    
    return [TextContent(
        type="text",
        text=format_response({
            "holdings": holdings,
            "summary": {
                "total_stocks": len(holdings),
                "total_investment": f"₹{total_investment:,.2f}",
                "current_value": f"₹{total_current:,.2f}",
                "total_pnl": f"₹{total_pnl:,.2f}",
                "pnl_percentage": f"{(total_pnl/total_investment*100):.2f}%"
            }
        })
    )]
```

### 6. Placing Orders

> *"For order placement, we automatically detect market hours and use the appropriate order variety."*

```python
elif name == "buy_stock":
    symbol = arguments.get("symbol")
    quantity = arguments.get("quantity")
    price = arguments.get("price")
    product = arguments.get("product", "CNC")
    variety = get_order_variety()  # Automatically 'regular' or 'amo'
    
    order = kc.place_order(
        variety=variety,
        exchange="NSE",
        tradingsymbol=symbol,
        transaction_type="BUY",
        quantity=quantity,
        product=product,
        order_type="LIMIT",
        price=price,
        validity="DAY"
    )
    
    return [TextContent(
        type="text",
        text=format_response({
            "success": True,
            "order_id": order,
            "variety": variety,
            "message": f"Buy order placed for {quantity} shares of {symbol} at ₹{price}",
            "market_status": "Market is OPEN" if is_market_open() else "Market is CLOSED (AMO order)"
        })
    )]
```

---

## 💻 SLIDE 10: CODE WALKTHROUGH - SERVER STARTUP (10:30 - 11:00)

### 7. Main Entry Point

> *"Finally, the main function starts the MCP server using stdio (standard input/output) transport. This allows Claude Desktop to communicate with our server."*

```python
async def main():
    """Start the MCP server for AI agent integration."""
    import sys
    print("🤖 Zerodha TradeBot MCP Server starting...", file=sys.stderr)
    print("📊 Waiting for AI agent connection via stdio...", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
```

> *"The `stdio_server()` context manager handles the communication protocol. The server runs asynchronously, waiting for tool calls from Claude."*

---

## 📱 SLIDE 11: LIVE DEMO (11:00 - 13:00)

> *"Let me show you the system in action with Claude Desktop."*

**Demo Scenarios:**

### Scenario 1: Portfolio Check
> *"I ask Claude: 'What stocks do I own?'"*
> *"Claude uses the `get_holdings` tool and shows me my portfolio with current P&L."*

### Scenario 2: Stock Price
> *"I ask: 'What's the current price of HDFCBANK?'"*
> *"Claude fetches real-time data using `get_quote` and shows last traded price, day high/low, volume."*

### Scenario 3: Placing an Order
> *"I say: 'Buy 5 shares of RELIANCE at ₹2500'"*
> *"Claude confirms the order type (regular or AMO based on market hours), places the order, and returns the order ID."*

---

## 🏗️ SLIDE 12: ARCHITECTURE (13:00 - 13:30)

**(Show architecture diagram)**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Claude AI     │────▶│   MCP Server    │────▶│  Kite Connect   │
│   (Desktop)     │◀────│  (trading_bot)  │◀────│     API         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     Natural              Tool Execution          Market Data &
     Language             & Response              Order Execution
```

> *"The MCP Server sits in the middle – translating between human intent and trading APIs."*

---

## ✅ SLIDE 13: CONCLUSION (13:30 - 14:00)

> *"To summarize:*
>
> 1. *We built an **MCP Server** that exposes Zerodha trading as AI-accessible tools.*
> 2. *Users can **trade using natural language** through Claude Desktop.*
> 3. *The system handles **authentication, market hours, and errors** automatically."*
>
> *"This project demonstrates how **AI agents can integrate with real-world financial APIs**, making complex systems accessible to everyone."*
>
> *"Thank you for watching!"*

---

## 📋 Quick Reference: Technology Stack

| Technology | Purpose |
|------------|---------|
| **Python** | Core backend language |
| **Kite Connect API** | Zerodha trading integration |
| **MCP Protocol** | AI agent tool exposure |
| **asyncio** | Asynchronous operations |
| **Claude AI** | Natural language interface |

---

## 📁 Project Structure

| File | Purpose |
|------|---------|
| `trading_bot.py` | Main MCP Server (472 lines) |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment template |
| `README.md` | Documentation |

---

## 🎯 Interview Talking Points

1. **Why MCP?** – "MCP is the emerging standard for AI tool integration, supported by Anthropic. It provides a secure, standardized way for AI to access external services."

2. **Why Python?** – "Python has excellent async support and the official Kite Connect SDK, making it ideal for this integration."

3. **Real-World Application** – "This could be extended to support voice assistants, Telegram bots, or any AI interface."

4. **Security** – "API keys are stored in environment variables, access tokens are session-based, and the MCP protocol ensures only authorized operations."
