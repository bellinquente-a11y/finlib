from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, BaseModel
from datetime import datetime

class BinanceSettings(BaseModel):
    url: str = "https://api.binance.com/api/v3/klines"
    rows: tuple[str, ...] = ("open_time", "open", "high", "low", "close", "volume", "close_time", 
                     "quote_asset_volume", "number_of_trades", "taker_buy_quote_asset_volume", "ignore")
    first_date: datetime = datetime(2015,1,1)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__",)

    data_dir: str = Field(default='./data')
    fetch_timeout_seconds: float = Field(default=10.0)
    log_level: str = Field(default='INFO')

    binance: BinanceSettings = BinanceSettings()

settings = Settings()  # auto-loads from .env or environment