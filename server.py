import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from metaapi_cloud_sdk import MetaApi

app = FastAPI(title="MT5 Execution Bridge")

# Retrieve API keys from environment variables
API_TOKEN = os.getenv("API_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

if not API_TOKEN or not ACCOUNT_ID:
    raise RuntimeError("API_TOKEN or ACCOUNT_ID environment variable is missing.")

# Initialize MetaAPI SDK
api = MetaApi(token=API_TOKEN)

class TradeRequest(BaseModel):
    symbol: str = "XAUUSD"
    action: str  # "BUY" or "SELL"
    num_trades: int = 1
    volume: float = 0.01

@app.get("/")
def root():
    return {"status": "online", "message": "MetaAPI MT5 Bridge Running"}

@app.post("/execute")
async def execute_trade(trade: TradeRequest):
    try:
        # Retrieve MT5 account instance
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        
        # Ensure account connection is active
        if account.state != "DEPLOYED":
            await account.deploy()
        await account.wait_connected()
        
        # Connect via RPC connection
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        
        action = trade.action.upper()
        results = []

        # Execute multiple positions concurrently
        for i in range(trade.num_trades):
            if action == "BUY":
                result = await connection.create_market_buy_order(
                    symbol=trade.symbol,
                    volume=trade.volume
                )
            elif action == "SELL":
                result = await connection.create_market_sell_order(
                    symbol=trade.symbol,
                    volume=trade.volume
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid action. Use 'BUY' or 'SELL'.")
            
            results.append(result)

        return {
            "status": "success",
            "executed_trades": len(results),
            "symbol": trade.symbol,
            "action": action,
            "details": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
