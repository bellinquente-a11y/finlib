from fastapi import FastAPI

from finlib.api.routes import market_data, portfolio

app = FastAPI()
app.include_router(market_data.router)
app.include_router(portfolio.router)
