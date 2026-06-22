from finlib import calculate_daily_vwap, Trade
from pathlib import Path
import pytest
from decimal import Decimal
from finlib.analytics import group_trades_by_symbol, trade_summary

def test_calculate_daily_vwap_path_exists():
    with pytest.raises(Exception):
        _ = calculate_daily_vwap(Path("xyz"), "AAPL")

def test_calculate_daily_vwap_missing_symbol(tmp_path):
    csv_file = tmp_path / "prices.csv"
    columns = "symbol,timestamp,open,high,low,close,volume\n"
    line = "AAPL,2026-01-02T09:30:00,195,195.3,194.75,195.28,1551595\n"
    csv_file.write_text(f"{columns}{line}")
    with pytest.raises(Exception):
        _ = calculate_daily_vwap(csv_file, "XYZ")

def test_group_trades_by_symbol_result():
    trades = [Trade(symbol='BHP', quantity=Decimal(100), price=Decimal('45.50'), side='BUY'),
              Trade(symbol='AAP', quantity=Decimal(200), price=Decimal('10.00'), side='SELL'),
              Trade(symbol='BHP', quantity=Decimal(200), price=Decimal('45.50'), side='BUY')
              ]
    group = group_trades_by_symbol(trades)
    assert group == {"AAP": [trades[1]], "BHP": [trades[0], trades[2]]}

def test_group_trades_by_symbol_input_type():
    trades = [Trade(symbol='BHP', quantity=Decimal(100), price=Decimal('45.50'), side='BUY'),
              Trade(symbol='AAP', quantity=Decimal(200), price=Decimal('10.00'), side='SELL'),
              None
              ]
    with pytest.raises(TypeError):
        _ = group_trades_by_symbol(trades)

def test_trade_summary_input_type():
    trades = [Trade(symbol='BHP', quantity=Decimal(100), price=Decimal('45.50'), side='BUY'),
              Trade(symbol='AAP', quantity=Decimal(200), price=Decimal('10.00'), side='SELL'),
              None
              ]
    with pytest.raises(TypeError):
        trade_summary(trades)

def test_trade_summary_empty_list():
    with pytest.raises(Exception):
        trade_summary([])

def test_trade_summary_calculation(capsys):
    trades = [Trade(symbol='BHP', quantity=Decimal(100), price=Decimal('45.50'), side='BUY'),
              Trade(symbol='AAP', quantity=Decimal(200), price=Decimal('10.00'), side='SELL'),
              Trade(symbol='BHP', quantity=Decimal(200), price=Decimal('45.50'), side='BUY')
              ]    
    trade_summary(trades)
    captured = capsys.readouterr()
    expected = "AAP: 1 trades; quantity = 200; notional = -2000.00\nBHP: 2 trades; quantity = 300; notional = 13650.00\n"
    assert captured.out==expected