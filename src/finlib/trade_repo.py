from typing import Protocol, runtime_checkable
from finlib.models import Trade
from decimal import Decimal
from pathlib import Path

@runtime_checkable
class TradeRepository(Protocol):
    def add(self, trade: Trade) -> None: ...
    def get_all(self) -> list[Trade]: ...
    def get_by_symbol(self, symbol: str) -> list[Trade]: ...

class InMemoryTradeRepository:
    def __init__(self) -> None:
        self._trades: list[Trade] = []

    def add(self, trade: Trade) -> None:
        self._trades.append(trade)

    def get_all(self) -> list[Trade]:
        return list(self._trades)

    def get_by_symbol(self, symbol: str) -> list[Trade]:
        return [*filter(lambda t: t.symbol==symbol, self._trades)]
    

def _asserts_in_memory_trade_repo(x: InMemoryTradeRepository) -> TradeRepository:
    return x

class InFileTradeRepository:
    def __init__(self, filepath: Path) -> None:
        self._filepath = filepath

    def add(self, trade: Trade) -> None:
        with self._filepath.open("a") as f:
            f.write(trade.model_dump_json() + "\n")
    
    def get_all(self) -> list[Trade]:
        if not self._filepath.exists():
            return []
        else:
            with self._filepath.open() as f:
                return [Trade.model_validate_json(line) for line in f if line.strip()]
    
    def get_by_symbol(self, symbol: str) -> list[Trade]:
        if not self._filepath.exists():
            return []
        else:
            with self._filepath.open() as f:
                all_trades = (Trade.model_validate_json(line) for line in f if line.strip())
                return [*filter(lambda t: t.symbol==symbol, all_trades)]    


class PortfolioService():
    def __init__(self, trade_repo: TradeRepository):
        self._trade_repo = trade_repo

    def record_trade(self, trade: Trade) -> None:
        self._trade_repo.add(trade)

    def get_notional(self, symbol: str) -> Decimal:
        trades = self._trade_repo.get_by_symbol(symbol)
        return Decimal(sum(t.notional for t in trades))

    def get_position(self, symbol: str) -> Decimal:
        trades = self._trade_repo.get_by_symbol(symbol)
        return Decimal(sum(t.lot_size() for t in trades))

    def get_summary(self) -> dict[str, dict[str, Decimal]]:
        symbols = sorted(list(set(t.symbol for t in self._trade_repo.get_all())))
        return {
            symbol: {"position": self.get_position(symbol),
                     "notional": self.get_notional(symbol)
                    } 
                for symbol in symbols
            }