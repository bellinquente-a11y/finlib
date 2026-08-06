from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends

from finlib.api.deps import get_market_data_repo, get_trade_repo, require_key
from finlib.models import Trade
from finlib.ohlcv_repo import OHLCVRepository
from finlib.pipeline.analytics import compute_portfolio_performance_metrics
from finlib.portfolio import Portfolio
from finlib.trade_repo import TradeRepository

router = APIRouter()


@router.post("/trades", response_model=Trade, status_code=201, dependencies=[Depends(require_key)])
def add_trade(
    trade: Trade, trade_repo: Annotated[TradeRepository, Depends(get_trade_repo)]
) -> Trade:
    trade_repo.add(trade)
    return trade


@router.get("/trades", dependencies=[Depends(require_key)])
def trades(trade_repo: Annotated[TradeRepository, Depends(get_trade_repo)]) -> list[Trade]:
    return trade_repo.get_all()


@router.get("/positions", dependencies=[Depends(require_key)])
def positions(
    trade_repo: Annotated[TradeRepository, Depends(get_trade_repo)],
) -> dict[str, dict[str, Any]]:
    portfolio = Portfolio(name="portfolio", trades=trade_repo.get_all())
    positions = portfolio.historic_position()
    positions.index = positions.index.map(lambda d: d.isoformat())
    positions.columns = positions.columns.astype(str)
    return cast(dict[str, dict[str, Any]], positions.to_dict("index"))


@router.get("/pnl", dependencies=[Depends(require_key)])
def pnl(
    trade_repo: Annotated[TradeRepository, Depends(get_trade_repo)],
    market_data_repo: Annotated[OHLCVRepository, Depends(get_market_data_repo)],
) -> dict[str, dict[str, Any]]:
    # TODO on the endpoint saying "prices may be stale; refresh is deferred to a
    # scheduled ingestion job
    pnl, _, _ = compute_portfolio_performance_metrics(trade_repo, market_data_repo)
    pnl.index = pnl.index.map(lambda d: d.isoformat())
    pnl.columns = pnl.columns.astype(str)
    return cast(dict[str, dict[str, Any]], pnl.to_dict("index"))
