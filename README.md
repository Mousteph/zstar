https://github.com/user-attachments/assets/91c7c6b0-fa99-4624-80f1-5554134992d2

# Z* (ZStar)

Lightweight backtesting framework for running Python trading strategies from a CLI, a FastAPI backend, or a React web UI.

## What It Solves

ZStar gives you a small local workflow for testing a strategy against historical market data without building your own engine, API, and dashboard first.

## How It Works

1. You define a Python strategy class that inherits from `CoreStrategy`.
2. ZStar loads OHLCV data from Yahoo Finance.
3. The backtest engine applies your signals, position sizing, fees, and slippage.
4. Results are returned in the UI/API or written by the CLI as KPI JSON and an equity-curve HTML report.

## Main Capabilities

- Run backtests from the web UI, CLI, or Python code
- Load strategy code dynamically
- Configure fees, slippage, seed, balance, symbol, and date range
- Return KPIs, trades, market candles, and equity curve data

## Prerequisites

- Python 3.10+
- `pip`
- Docker and Docker Compose
- Optional for local UI development: Node.js and `npm`

## Installation

```bash
git clone git@github.com:Mousteph/zstar.git
cd zstar
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config_example.yaml config.yaml
```

`config.yaml` controls backend host, port, and allowed origins.

## Quick Start

### Web UI with Docker (recommended)

```bash
docker compose --profile dev up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

If you use the AI assistant from Docker, run Ollama on your host machine first:

```bash
ollama serve
ollama pull gemma4:e4b
```

The backend containers are configured to reach Ollama through `http://host.docker.internal:11434`.

### CLI backtest

```bash
python -m zstar.cli backtest \
  --strategy-file examples/cli/strategy.py \
  --config-file examples/cli/cli_config.yaml
```

Default CLI outputs:

- `outputs/kpis.json`
- `outputs/equity_curve.html`

## Local Development

Backend:

```bash
python -m zstar.api
```

Frontend:

```bash
cd webui
npm ci
npm run dev
```

The Vite dev server proxies `/api` requests to `http://localhost:8000` by default.

## Use From Python

```python
from zstar import CoreStrategy
from zstar.core.backtest import BacktesterEngine, BacktestConfigModel
from zstar.core.data_loader import DataLoaderConfigModel, YahooData


class BuyAndHoldStrategy(CoreStrategy):
    def long_entry_signals(self, data):
        data["long_entry"] = 0
        data.loc[data.index[0], "long_entry"] = 1
        return data

    def long_exit_signals(self, data):
        data["long_exit"] = 0
        data.loc[data.index[-1], "long_exit"] = 1
        return data

    def position_size(self, balance: float, entry_price: float) -> float:
        return round(balance / entry_price, 4)


data_config = DataLoaderConfigModel(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2025-01-01",
    interval="1d",
)

backtest_config = BacktestConfigModel(
    initial_balance=100000,
    entry_fee_pct=0.05,
    exit_fee_pct=0.05,
    slippage_pct=0.02,
    slippage_seed=42,
)

engine = BacktesterEngine(BuyAndHoldStrategy(), YahooData(data_config), backtest_config)
report = engine.run_backtest()

print(report.kpis())
print(report.equity_curve().tail())
```

For dynamic strategy files used by the UI or CLI, define exactly one `CoreStrategy` subclass and ZStar will inject `CoreStrategy`, `pd`, and `np` automatically.

## Validation

```bash
python -m pytest -q
```

## Roadmap

Planned directions for ZStar:

- Support additional market data sources beyond Yahoo Finance
- Add paper trading and live monitoring workflows
- Add optimization tools such as parameter tuning and walk-forward testing
- Add an AI assistant in the Web UI to help explain strategies and backtest results
