https://github.com/user-attachments/assets/52541fac-0e0f-43ee-9608-85554373bd20

# Z* (ZStar)

Lightweight backtesting framework for running Python trading strategies from a FastAPI backend, a Next.js web UI, or direct Python imports.

## Documentation

- [Core strategy contract](docs/core-strategy.md)
- [Backtest engine flow](docs/engine.md)
- [Backtesting metrics reference](docs/metrics.md)

## What It Solves

ZStar gives you a local workflow for testing a trading strategy against historical market data without having to build the engine, API, and dashboard yourself.

## How It Works

1. You define a Python strategy class that inherits from `CoreStrategy`.
2. ZStar loads OHLCV data from Yahoo Finance or from a CSV file.
3. The backtest engine applies your signals, position sizing, fees, and slippage bar by bar.
4. Results are returned as KPIs, trades, market candles, and an equity curve.

## Main Capabilities

- Run backtests from the web UI or Python code
- Load strategy files dynamically and validate them before execution
- Configure balance, fees, slippage, seed, symbol, and date range
- Inspect KPIs, trades, market data, and equity curve output

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
```

The repository expects a `config.yaml` file in the project root by default.

## Quick Start

### Docker Compose

The easiest way to run the full stack is:

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

### Backend Only

Run the FastAPI backend directly with the default config:

```bash
python -m zstar
```

You can also pass an explicit config path:

```bash
python -m zstar custom-config.yaml
```

The equivalent API module entrypoint is also available:

```bash
python -m zstar.api
python -m zstar.api custom-config.yaml
```

### Frontend Only

```bash
cd webui
npm ci
node scripts/start-next.mjs dev
```

When the frontend runs outside Docker, set `frontend.backend_proxy_url` to `http://localhost:8000` so the Next.js server can proxy `/api/...` requests to the backend.

## Configuration

ZStar loads `config.yaml` on startup. Docker mounts the repository config into both containers, and local commands read the same file by default.

```yaml
backend:
  host: "0.0.0.0"
  port: 8000
  allow_origins:
    - "http://localhost:3000"
    - "http://127.0.0.1:3000"
frontend:
  host: "0.0.0.0"
  port: 3000
  backend_proxy_url: "http://backend:8000"
paths:
  strategies_dir: "strategies"
  data_dir: "data"
  default_strategy_name: "default_strategy"
logging:
  level: "DEBUG"
  directory: "logs"
  filename: "app.log"
  max_bytes: 10485760
  backup_count: 5
  stdout: true
```

### Config Fields

| Field | Purpose | Notes |
| --- | --- | --- |
| `backend.host` | Bind address for the FastAPI server | Use `0.0.0.0` in Docker or local network access. |
| `backend.port` | Backend port | Must be an integer from `1` to `65535`. |
| `backend.allow_origins` | CORS allow-list | Use full `http://` or `https://` origins. |
| `frontend.host` | Bind address for the Next.js server | Usually `0.0.0.0` in Docker. |
| `frontend.port` | Frontend port | Must be an integer from `1` to `65535`. |
| `frontend.backend_proxy_url` | Backend URL used by the frontend proxy | Use `http://backend:8000` in Docker and `http://localhost:8000` for local frontend development. |
| `paths.strategies_dir` | Directory that stores strategy files | Must already exist on disk. |
| `paths.data_dir` | Directory that stores local data files | Created automatically if it does not exist. |
| `paths.default_strategy_name` | Default strategy filename stem | Used when a request does not provide a strategy name. |
| `logging.level` | Minimum log level | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `logging.directory` | Directory for log files | Relative paths are resolved from the config file location. |
| `logging.filename` | Log filename | Must be a base filename, not a path. |
| `logging.max_bytes` | Rotation threshold | Default is `10 MB`. |
| `logging.backup_count` | Number of rotated log files to keep | Default is `5`. |
| `logging.stdout` | Mirror logs to stdout | Useful in Docker and during development. |

### Configuration Notes

- `paths.strategies_dir` must point to a real directory before startup succeeds.
- `paths.data_dir` is created automatically if it does not exist.
- When using Docker, keep `backend.port` at `8000` and `frontend.port` at `3000`, or update the Compose port mappings at the same time.
- `backend.allow_origins` should include every browser origin that needs to call the API.

## Use From Python

You can run the backtester directly from code without the web UI.

```python
from zstar import CoreStrategy, BacktesterEngine
from zstar.core.backtest import BacktestConfigModel
from zstar.core.data_loader import YahooData


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


data_handler = YahooData(
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

engine = BacktesterEngine(BuyAndHoldStrategy(), data_handler, backtest_config)
report = engine.run_backtest()

print(report.kpis())
print(report.equity_curve().tail())
```

If you want to load strategy code dynamically, import `load_strategy_from_code` from `zstar.core.strategy` and make sure the code defines exactly one `CoreStrategy` subclass.

The repository also includes `strategies/default_strategy.py` as a reference strategy implementation.

## Validation

```bash
python -m pytest -q
```

## Reference Docs

Use these pages when you want the implementation details instead of the quick start:

- [`docs/core-strategy.md`](docs/core-strategy.md)
- [`docs/engine.md`](docs/engine.md)
- [`docs/metrics.md`](docs/metrics.md)
