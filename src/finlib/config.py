from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, BaseModel
from datetime import datetime

class BinanceSettings(BaseModel):
    """Settings for loading data from Binance"""
    url: str = "https://api.binance.com/api/v3/klines"
    columns: tuple[str, ...] = ("open_time", "open", "high", "low", "close", "volume", "close_time", 
                                "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", 
                                "taker_buy_quote_asset_volume", "ignore")
    columns_type: dict[str, type[int] | type[str]] = {"open_time": int,
                                                      "open": str, 
                                                      "high": str, 
                                                      "low": str, 
                                                      "close": str, 
                                                      "volume": str, 
                                                      "close_time": int, 
                                                      "quote_asset_volume": str, 
                                                      "number_of_trades": int, 
                                                      "taker_buy_base_asset_volume": str, 
                                                      "taker_buy_quote_asset_volume": str, 
                                                      "ignore": str
                                                      }
    first_date: datetime = datetime(2015,1,1)

class Settings(BaseSettings):
    """FINLIB project settings"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__",)

    data_dir: str = Field(default='./data')
    fetch_timeout_seconds: float = Field(default=10.0)
    log_level: str = Field(default='INFO')

    binance: BinanceSettings = BinanceSettings()

settings = Settings()  # auto-loads from .env or environment