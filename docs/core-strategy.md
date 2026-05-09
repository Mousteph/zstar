# Core Strategy Contract

`CoreStrategy` is the abstract base class every ZStar strategy must inherit from.
The backtester calls its methods in a fixed order, and the validation layer checks that the strategy returns the columns and values the engine expects.

## Strategy Responsibilities

A strategy is responsible for:

- building indicators from the input OHLCV data
- producing entry and exit signals
- optionally defining take-profit and stop-loss price series
- returning a positive numeric position size for each trade

## Base Class Methods

| Method | Default behavior | What it should return |
| --- | --- | --- |
| `calculate_indicators(data)` | Returns the input data unchanged | The same DataFrame, usually with extra indicator columns |
| `long_entry_signals(data)` | Adds `long_entry = 0` | A DataFrame containing a binary long-entry column |
| `short_entry_signals(data)` | Adds `short_entry = 0` | A DataFrame containing a binary short-entry column |
| `long_exit_signals(data)` | Adds `long_exit = 0` | A DataFrame containing a binary long-exit column |
| `short_exit_signals(data)` | Adds `short_exit = 0` | A DataFrame containing a binary short-exit column |
| `long_take_profit_signals(data)` | Adds `long_take_profit = NaN` | A DataFrame with numeric take-profit prices or `NaN` |
| `short_take_profit_signals(data)` | Adds `short_take_profit = NaN` | A DataFrame with numeric take-profit prices or `NaN` |
| `long_stop_loss_signals(data)` | Adds `long_stop_loss = NaN` | A DataFrame with numeric stop-loss prices or `NaN` |
| `short_stop_loss_signals(data)` | Adds `short_stop_loss = NaN` | A DataFrame with numeric stop-loss prices or `NaN` |
| `position_size(balance, entry_price)` | Abstract | A finite positive numeric size |

## Signal Rules

The backtester only treats `True` and `1` as active signals.

- Use `0` or `False` for inactive bars.
- Use `1` or `True` for active bars.
- Missing values are allowed for non-signal rows, but signal validation will reject values outside the binary set.

Risk-price columns follow a different rule:

- numeric values are interpreted as explicit price levels
- `NaN` means the strategy does not want a take-profit or stop-loss for that bar

## `position_size()`

`position_size(balance, entry_price)` is required and must return:

- a finite number
- greater than zero
- suitable for direct use as the trade size

During validation, ZStar calls `position_size(10000, 100)` to ensure the implementation is usable before a backtest starts.

## Loading Strategies From Code

Use `load_strategy_from_code()` when the strategy code is stored as a string.

```python
from zstar.core.strategy import load_strategy_from_code

code = """
from zstar.core.strategy import CoreStrategy

class MyStrategy(CoreStrategy):
    def long_entry_signals(self, data):
        data["long_entry"] = 0
        data.loc[data.index[0], "long_entry"] = 1
        return data

    def long_exit_signals(self, data):
        data["long_exit"] = 0
        data.loc[data.index[-1], "long_exit"] = 1
        return data

    def position_size(self, balance, entry_price):
        return balance / entry_price
"""

strategy = load_strategy_from_code(code)
```

What happens internally:

1. ZStar validates the code with `ValidateStrategy`.
2. The code must define exactly one subclass of `CoreStrategy`.
3. Any syntax, import, runtime, or contract errors are returned as a `StrategyValidationError`.
4. If validation passes, ZStar instantiates the strategy and returns it.

For strategy files on disk, relative imports from the same strategy directory are supported.
If your strategy code uses `pandas`, `numpy`, or other helpers, import them inside the strategy file or string yourself.

## Example: Long-Only Crossover Strategy

```python
import pandas as pd
from zstar.core.strategy import CoreStrategy


class SimpleTrendStrategy(CoreStrategy):
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        data["fast"] = data["close"].rolling(window=10, min_periods=1).mean()
        data["slow"] = data["close"].rolling(window=30, min_periods=1).mean()
        return data

    def long_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_entry"] = ((data["fast"] > data["slow"]) & (data["fast"].shift(1) <= data["slow"].shift(1))).astype(int)
        return data

    def long_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_exit"] = ((data["fast"] < data["slow"]) & (data["fast"].shift(1) >= data["slow"].shift(1))).astype(int)
        return data

    def short_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_entry"] = 0
        return data

    def short_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_exit"] = 0
        return data

    def position_size(self, balance: float, entry_price: float) -> float:
        return round(balance / entry_price, 4)
```

## Example: Strategy With Fixed Risk Levels

```python
import pandas as pd
from zstar.core.strategy import CoreStrategy


class FixedRiskStrategy(CoreStrategy):
    def long_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_entry"] = 0
        data.loc[data.index[5], "long_entry"] = 1
        return data

    def long_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_exit"] = 0
        data.loc[data.index[15], "long_exit"] = 1
        return data

    def long_take_profit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_take_profit"] = data["close"] * 1.05
        return data

    def long_stop_loss_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_stop_loss"] = data["close"] * 0.98
        return data

    def short_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_entry"] = 0
        return data

    def short_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_exit"] = 0
        return data

    def position_size(self, balance: float, entry_price: float) -> float:
        return max(1.0, round(balance * 0.1 / entry_price, 4))
```

## Validation Expectations

The validator checks that:

- the strategy code parses correctly
- exactly one `CoreStrategy` subclass exists
- the signal columns are present after the strategy methods run
- signal values are binary
- risk columns are numeric where provided
- `position_size()` returns a finite positive numeric value

If any of those checks fail, the strategy is rejected before the backtest starts.
