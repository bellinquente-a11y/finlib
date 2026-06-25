from typing import Protocol, runtime_checkable
from finlib.models import Trade
from decimal import Decimal

@runtime_checkable
class TradeRepository(Protocol):
    def add(self, trade: Trade) -> None: ...
    def get_all(self) -> list[Trade]: ...
    def get_by_symbol(self, symbol: str) -> list[Trade]: ...
    def get_all_symbols(self) -> list[str]: ...

class InMemoryTradeRepository:
    def __init__(self) -> None:
        self._trades: list[Trade] = []
        self._symbols: set[str] = set()

    def add(self, trade: Trade) -> None:
        self._trades.append(trade)
        self._symbols.add(trade.symbol)

    def get_all(self) -> list[Trade]:
        return list(self._trades)

    def get_by_symbol(self, symbol: str) -> list[Trade]:
        if symbol not in self._symbols:
            raise ValueError
        return [t for t in self._trades if t.symbol == symbol]

    def get_all_symbols(self) -> list[str]:
        return sorted(list(self._symbols))
    

def _asserts_in_memory_trade_repo(x: InMemoryTradeRepository) -> TradeRepository:
    return x


class PortfolioService():
    def __init__(self, trade_repo: TradeRepository):
        self._trade_repo = trade_repo

    def record_trade(self, trade: Trade) -> None:
        self._trade_repo.add(trade)

    def get_position(self, symbol: str) -> Decimal:
        trades = self._trade_repo.get_by_symbol(symbol)
        return Decimal(sum([t.lot_size() for t in trades]))

    def get_summary(self) -> dict[str, Decimal]:
        symbols = self._trade_repo.get_all_symbols()
        return {symbol: self.get_position(symbol) for symbol in symbols}