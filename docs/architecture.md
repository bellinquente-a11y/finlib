# Pipeline

The finlib pipeline loads trade data and fetches market data to analyse the portfolio PnL.

```mermaid
sequenceDiagram
    participant CLI
    participant config
    participant TradeRepo
    participant OHLCVRepo
    participant MarketDataAnalytics
    participant PortfolioService
    participant PortfolioPnlAnaltics
    participant Output
    CLI->>TradeRepo: trades.jsonl
    config->>OHLCVRepo: repo_dir, freq
    TradeRepo->>OHLCVRepo: symbols
    OHLCVRepo-->>MarketDataAnalytics: calculate 
    TradeRepo->>PortfolioService: positions
    OHLCVRepo->>PortfolioService" mark to market
    PortfolioService->PortfolioPnlAnaltics: calculate
    MarketDataAnalytics-->Output: print
    PortfolioPnlAnaltics->Output: print
```



