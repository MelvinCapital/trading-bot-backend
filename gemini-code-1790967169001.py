from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from metaapi_cloud_sdk import MetaApi
import os
import uvicorn

app = FastAPI(title="Trading Bot Remote Server")

# Retrieve credentials from Render Environment Variables
API_TOKEN = os.getenv("API_TOKEN", "YOUR_METAAPI_TOKEN_HERE")
ACCOUNT_ID = os.getenv("ACCOUNT_ID", "YOUR_METAAPI_ACCOUNT_ID_HERE")

# Initialize MetaAPI SDK
api = MetaApi(token=API_TOKEN)

class TradeRequest(BaseModel):
    symbol: str = "XAUUSD"      # Default pair: Gold
    action: str = "BUY"         # BUY or SELL
    num_trades: int = 5         # Number of batch trades
    volume: float = 0.01        # Lot size

@app.get("/")
async def root():
    return {"status": "Trading Bot Server is Running"}

@app.post("/execute")
async def execute_batch_trade(request: TradeRequest):
    try:
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()

        results = []
        for i in range(request.num_trades):
            if request.action.upper() == "BUY":
                order = await connection.create_market_buy_order(
                    symbol=request.symbol, 
                    volume=request.volume
                )
            elif request.action.upper() == "SELL":
                order = await connection.create_market_sell_order(
                    symbol=request.symbol, 
                    volume=request.volume
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid action type. Use BUY or SELL.")
            
            results.append(order['orderId'])

        return {
            "status": "success",
            "executed_trades": len(results),
            "order_ids": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/account-info")
async def get_account_info():
    try:
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        
        information = await connection.get_account_information()
        return information
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)