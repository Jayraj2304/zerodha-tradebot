# 🤖 ZERODHA TRADEBOT - AI-Powered Trading Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![Kite Connect](https://img.shields.io/badge/Kite_Connect-API-orange?style=for-the-badge)
![MCP](https://img.shields.io/badge/MCP-Server-purple?style=for-the-badge)

**A back-end system that provides real-time portfolio insights by integrating AI capabilities with Zerodha's Kite Connect APIs via the MCP (Model Context Protocol) server.**

[Demo Video](#-demo) • [Features](#-features) • [Installation](#-installation--setup) • [Architecture](#-architecture)

</div>

---

## 📋 Project Overview

The **ZERODHA TRADEBOT** is an AI-powered trading assistant that bridges the gap between conversational AI and real-world trading operations. By implementing Anthropic's **Model Context Protocol (MCP)**, this system exposes trading functionality as tools that AI agents (like Claude) can use to provide natural language trading assistance.

### ✨ Key Highlights

- 🔄 **Real-time Trading**: Execute buy/sell orders directly through natural language
- 📊 **Portfolio Insights**: View holdings, positions, and P&L in real-time
- ⏰ **Smart Order Handling**: Automatically uses AMO (After Market Orders) outside trading hours
- 🔐 **Secure Authentication**: Implements Zerodha's OAuth-based authentication flow

---

## 🎬 Demo

📹 **Video Walkthrough**: [ZERODHA_TRADEBOT_DEMO.mp4](./ZERODHA_TRADEBOT_DEMO.mp4)

The demo showcases:
- Authentication flow with Zerodha
- Fetching portfolio holdings
- Checking real-time stock prices
- Placing buy/sell orders via AI conversation

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.10+** | Core backend language |
| **Kite Connect API** | Zerodha trading integration |
| **MCP Server** | AI agent tool protocol |
| **asyncio** | Asynchronous operations |
| **dotenv** | Environment configuration |

---

## 📦 Features & Available Tools

### Authentication Tools
| Tool | Description |
|------|-------------|
| `get_login_url` | Generate Kite login URL for OAuth authentication |
| `generate_access_token` | Generate access token from request token |
| `set_access_token` | Manually set an existing access token |

### Portfolio & Account Tools
| Tool | Description |
|------|-------------|
| `get_profile` | Get user profile and account info |
| `get_holdings` | Get all stock holdings with P&L summary |
| `get_positions` | Get current day positions (intraday & delivery) |
| `get_orders` | Get all orders placed today with status |
| `get_margins` | Get available funds/margins |

### Market Data Tools
| Tool | Description |
|------|-------------|
| `get_ltp` | Get last traded price for multiple stocks |
| `get_market_status` | Check if market is open/closed |

### Trading Tools
| Tool | Description |
|------|-------------|
| `buy_stock` | Place a buy order (LIMIT) |
| `sell_stock` | Place a sell order (LIMIT) |
| `cancel_order` | Cancel a pending order |
| `get_order_history` | Get complete history of an order |

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Zerodha Kite Connect API credentials
- Claude Desktop (for AI integration)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/zerodha-tradebot.git
cd zerodha-tradebot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file in the project root:
```env
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret
```

### 4. Run the Server
```bash
python trading_bot.py
```

---

## 🔧 Claude Desktop Configuration

To integrate with Claude Desktop, add this to your config file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "trading-bot": {
      "command": "python",
      "args": ["path/to/trading_bot.py"]
    }
  }
}
```

---

## 🏗️ Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│     Claude AI       │     │     MCP Server      │     │   Kite Connect      │
│     (Desktop)       │────▶│   (trading_bot.py)  │────▶│       API           │
│                     │◀────│                     │◀────│                     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
     Natural Language          Tool Execution &           Market Data &
        Interface              Response Handling          Order Execution
```

### Data Flow
1. User sends natural language request to Claude
2. Claude identifies the appropriate tool from MCP server
3. MCP server executes the Kite Connect API call
4. Response is formatted and returned to Claude
5. Claude presents the information in conversational format

---

## ⏰ Market Hours Handling

| Time Period | Order Type |
|-------------|------------|
| **9:15 AM - 3:30 PM IST** (Weekdays) | Regular Orders |
| Outside Market Hours | AMO (After Market Orders) |

The system automatically detects market status and places appropriate order types.

---

## 📝 Example Usage

Once connected to Claude, you can ask naturally:

```
💬 "What's my current portfolio?"
💬 "Show me the price of RELIANCE"
💬 "Buy 10 shares of HDFCBANK at ₹1600"
💬 "What are my available funds?"
💬 "Cancel order 123456789"
💬 "Is the market open right now?"
```

---

## 📁 Project Structure

```
TRADING_BOT/
├── trading_bot.py           # Main MCP Server (Python)
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── README.md               # Documentation
├── VIDEO_SCRIPT.md         # Demo script
└── ZERODHA_TRADEBOT_DEMO.mp4  # Demo video
```

---

## ⚠️ Important Notes

1. **Access Token Expiry**: Kite access tokens expire daily at 6:00 AM IST
2. **Real Orders**: This bot places **real orders** - use with caution!
3. **Weekend/Holidays**: Orders will be queued as AMO orders
4. **API Limits**: Be mindful of Kite Connect API rate limits

---

## 📜 License

This project is built for educational and demonstration purposes.

---

<div align="center">

**Author**: Jayra  
**Date**: December 2024

</div>
