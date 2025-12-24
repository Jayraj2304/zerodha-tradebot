"""
ZERODHA TRADEBOT - AI-Powered Trading Assistant
================================================
A back-end system that provides real-time portfolio insights by integrating 
AI capabilities with Zerodha's Kite Connect APIs via the MCP server protocol.

Technology Stack: Python, Kite Connect APIs, MCP Server

Author: Jayra
Date: January 2025
"""

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

# CONFIGURATION

KITE_API_KEY = os.getenv("KITE_API_KEY", "fjcyhcx8d2e6ienr")
KITE_API_SECRET = os.getenv("KITE_API_SECRET", "apwljgcz0focjpxm1581xcvnt3ua64ag")

# Initialize Kite Connect
kc = KiteConnect(api_key=KITE_API_KEY)
access_token: Optional[str] = None

# Initialize MCP Server
server = Server("trading-bot")

# HELPER FUNCTIONS

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


# MCP TOOL DEFINITIONS

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
            name="generate_access_token",
            description="Generate access token using request token from login",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_token": {"type": "string", "description": "Request token from login redirect"}
                },
                "required": ["request_token"]
            }
        ),
        Tool(
            name="set_access_token",
            description="Manually set an existing access token",
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Access token to set"}
                },
                "required": ["token"]
            }
        ),
        Tool(
            name="get_profile",
            description="Get user profile and account information from Zerodha",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_holdings",
            description="Get all stock holdings in the portfolio with current values and P&L",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_positions",
            description="Get current day positions (intraday and overnight)",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_orders",
            description="Get all orders placed today with their status",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_ltp",
            description="Get last traded price for one or more stocks",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of trading symbols (e.g., ['HDFCBANK', 'RELIANCE'])"
                    }
                },
                "required": ["symbols"]
            }
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
                    "product": {"type": "string", "enum": ["CNC", "MIS"], "default": "CNC", "description": "CNC for delivery, MIS for intraday"}
                },
                "required": ["symbol", "quantity", "price"]
            }
        ),
        Tool(
            name="sell_stock",
            description="Place a sell order for a stock. Uses regular order during market hours, AMO otherwise.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Trading symbol (e.g., HDFCBANK)"},
                    "quantity": {"type": "integer", "description": "Number of shares to sell"},
                    "price": {"type": "number", "description": "Limit price per share"},
                    "product": {"type": "string", "enum": ["CNC", "MIS"], "default": "CNC", "description": "CNC for delivery, MIS for intraday"}
                },
                "required": ["symbol", "quantity", "price"]
            }
        ),
        Tool(
            name="cancel_order",
            description="Cancel a pending order by order ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID to cancel"},
                    "variety": {"type": "string", "enum": ["regular", "amo"], "default": "regular", "description": "Order variety"}
                },
                "required": ["order_id"]
            }
        ),
        Tool(
            name="get_margins",
            description="Get available margins/funds in the trading account",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_market_status",
            description="Check if NSE market is currently open or closed",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_order_history",
            description="Get the complete history/trail of a specific order",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID to get history for"}
                },
                "required": ["order_id"]
            }
        )
    ]


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
                    "user_id": session.get("user_id"),
                    "user_name": session.get("user_name"),
                    "message": "Access token generated and set successfully! You can now use all trading tools.",
                    "expires_at": "Token expires at 6:00 AM IST tomorrow"
                })
            )]
        
        elif name == "set_access_token":
            token = arguments.get("token")
            access_token = token
            kc.set_access_token(access_token)
            
            # Verify token by getting profile
            profile = kc.profile()
            
            return [TextContent(
                type="text",
                text=format_response({
                    "success": True,
                    "message": "Access token set successfully!",
                    "user_id": profile.get("user_id"),
                    "user_name": profile.get("user_name"),
                    "email": profile.get("email")
                })
            )]
        
        # PROFILE & PORTFOLIO TOOLS
        elif name == "get_profile":
            profile = kc.profile()
            return [TextContent(type="text", text=format_response(profile))]
        
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
                        "pnl_percentage": f"{(total_pnl/total_investment*100):.2f}%" if total_investment > 0 else "0%"
                    }
                })
            )]
        
        elif name == "get_positions":
            positions = kc.positions()
            return [TextContent(type="text", text=format_response(positions))]
        
        elif name == "get_orders":
            orders = kc.orders()
            return [TextContent(type="text", text=format_response(orders))]
        
        # MARKET DATA TOOLS
        elif name == "get_quote":
            symbol = arguments.get("symbol")
            exchange = arguments.get("exchange", "NSE")
            instrument = f"{exchange}:{symbol}"
            
            quote = kc.quote([instrument])
            return [TextContent(type="text", text=format_response(quote))]
        
        elif name == "get_ltp":
            symbols = arguments.get("symbols", [])
            instruments = [f"NSE:{s}" for s in symbols]
            ltp = kc.ltp(instruments)
            return [TextContent(type="text", text=format_response(ltp))]
        
        # TRADING TOOLS
        elif name == "buy_stock":
            symbol = arguments.get("symbol")
            quantity = arguments.get("quantity")
            price = arguments.get("price")
            product = arguments.get("product", "CNC")
            variety = get_order_variety()
            
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
                    "message": f"Buy order placed successfully for {quantity} shares of {symbol} at ₹{price}",
                    "market_status": "Market is OPEN" if is_market_open() else "Market is CLOSED (AMO order)"
                })
            )]
        
        elif name == "sell_stock":
            symbol = arguments.get("symbol")
            quantity = arguments.get("quantity")
            price = arguments.get("price")
            product = arguments.get("product", "CNC")
            variety = get_order_variety()
            
            order = kc.place_order(
                variety=variety,
                exchange="NSE",
                tradingsymbol=symbol,
                transaction_type="SELL",
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
                    "message": f"Sell order placed successfully for {quantity} shares of {symbol} at ₹{price}",
                    "market_status": "Market is OPEN" if is_market_open() else "Market is CLOSED (AMO order)"
                })
            )]
        
        elif name == "cancel_order":
            order_id = arguments.get("order_id")
            variety = arguments.get("variety", "regular")
            
            result = kc.cancel_order(variety=variety, order_id=order_id)
            
            return [TextContent(
                type="text",
                text=format_response({
                    "success": True,
                    "order_id": result,
                    "message": f"Order {order_id} cancelled successfully"
                })
            )]
        
        # ACCOUNT TOOLS
        elif name == "get_margins":
            margins = kc.margins()
            return [TextContent(type="text", text=format_response(margins))]
        
        elif name == "get_market_status":
            return [TextContent(
                type="text",
                text=format_response({
                    "is_open": is_market_open(),
                    "status": "OPEN" if is_market_open() else "CLOSED",
                    "order_type_available": get_order_variety().upper(),
                    "market_hours": "9:15 AM - 3:30 PM IST (Monday to Friday)",
                    "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
                })
            )]
        
        elif name == "get_order_history":
            order_id = arguments.get("order_id")
            history = kc.order_history(order_id)
            return [TextContent(type="text", text=format_response(history))]
        
        else:
            return [TextContent(
                type="text",
                text=format_response({"error": f"Unknown tool: {name}"})
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=format_response({
                "error": str(e),
                "tool": name,
                "hint": "If authentication error, please use set_access_token or generate_access_token first"
            })
        )]


# MAIN ENTRY POINT

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
