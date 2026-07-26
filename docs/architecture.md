# Pipeline

The finlib pipeline loads trade data and fetches market data to analyse the portfolio PnL.

```mermaid
sequenceDiagram
    participant CLI
    participant config
    participant TradeRepo
    participant OHLCVRepository
    participant MarketDataAnalytics
    participant PortfolioService
    participant PortfolioPnlAnalytics
    participant Output
    CLI->>TradeRepo: trades.jsonl
    config->>OHLCVRepository: repo_dir, freq
    TradeRepo->>OHLCVRepository: symbols
    OHLCVRepository-->>MarketDataAnalytics: calculate
    TradeRepo->>PortfolioService: positions
    OHLCVRepository->>PortfolioService" mark to market
    PortfolioService->PortfolioPnlAnalytics: calculate
    MarketDataAnalytics-->Output: print
    PortfolioPnlAnalytics->Output: print
```
