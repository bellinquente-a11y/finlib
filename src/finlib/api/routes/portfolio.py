from typing import Annotated

from fastapi import APIRouter, Depends

from finlib.api.deps import get_trade_repo, require_key
from finlib.models import Trade
from finlib.trade_repo import TradeRepository

router = APIRouter()


@router.post("/trades", response_model=Trade, status_code=201, dependencies=[Depends(require_key)])
def add_trade(trade: Trade, repo: Annotated[TradeRepository, Depends(get_trade_repo)]) -> Trade:
    repo.add(trade)
    return trade


@router.get("/trades", dependencies=[Depends(require_key)])
def trades(repo: Annotated[TradeRepository, Depends(get_trade_repo)]) -> list[Trade]:
    return repo.get_all()
