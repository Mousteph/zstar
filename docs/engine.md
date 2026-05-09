# Backtest Engine Flow

`BacktesterEngine` is the runtime that turns a strategy, a data source, and a backtest configuration into a `BacktestReport`.

## Inputs

The engine needs three things:

- a `CoreStrategy` implementation
- a `DataHandler` that returns OHLCV data and the interval string
- a `BacktestConfigModel` with balance, fee, and slippage settings

## High-Level Lifecycle

1. Reset the engine state.
2. Copy market data from the data handler.
3. Run the strategy methods in a fixed sequence to add indicators and signal columns.
4. Walk through the bars one row at a time.
5. Execute pending opens and closes at the bar open.
6. Check intrabar stop-loss and take-profit conditions.
7. Mark open positions for close when an exit signal appears.
8. Queue new entries when the portfolio is flat.
9. Force-close any still-open position at the last close.
10. Build the final `BacktestReport`.

## Strategy Preparation Order

Before the loop starts, ZStar applies strategy methods in this exact order:

1. `calculate_indicators`
2. `long_entry_signals`
3. `short_entry_signals`
4. `long_exit_signals`
5. `short_exit_signals`
6. `long_take_profit_signals`
7. `short_take_profit_signals`
8. `long_stop_loss_signals`
9. `short_stop_loss_signals`

That order matters because later methods can depend on columns created earlier.

## Per-Bar Loop Order

For every bar, the engine uses the current row's open price as the execution price anchor and then applies the following logic:

1. If a position is marked `pending_close`, close it at the current open.
2. If a position is marked `pending_open`, open it at the current open.
3. Check whether an open position hit its stop-loss or take-profit within the current candle.
4. If the current open position has an exit signal, mark it `pending_close` for the next bar.
5. If the portfolio is flat and the long-entry signal is active, prepare a long order.
6. If the portfolio is still flat and the short-entry signal is active, prepare a short order.

## Important Execution Rules

### Entries Execute on the Next Bar Open

**Entry signals are prepared on the signal candle, then executed on the next bar open.**
That means the strategy decides on one row and the fill happens on the following row.

### Pending State Is Explicit

The portfolio keeps one open order and tracks its status:

- `PENDING_OPEN` means the signal has fired, but the order has not been filled yet
- `OPEN` means the trade is active
- `PENDING_CLOSE` means an exit signal has been seen and the position will close on the next bar open

### Stop-Loss and Take-Profit Are Intrabar

After a position is open, the engine checks the current bar's `high` and `low`:

- **stop-loss is checked before take-profit**

So if both levels are touched in the same candle, stop-loss wins because it is evaluated first.

### Risk Levels Come From the Signal Candle

Take-profit and stop-loss prices are read from the row that generated the entry signal.
When the entry actually fills, the engine validates those levels against the fill price:

- a long take-profit must be above the entry price
- a long stop-loss must be below the entry price
- a short take-profit must be below the entry price
- a short stop-loss must be above the entry price

**If the entry price has already crossed one of its risk levels at execution time, the entry is canceled.**

### Slippage Is Adverse and Seeded

When `slippage_pct` is greater than zero, fills are randomly adjusted against the trader:

- buys pay more
- sells receive less

`slippage_seed` makes the random sequence repeatable.

### Final Closeout

If a position is still open after the last bar, the engine closes it at the final close price and marks the trade with `exit_reason = "end_of_data"`.

## Report Construction

The engine returns a `BacktestReport` containing:

- `initial_balance`
- `final_balance`
- `trades`
- `data`
- `interval`

From that report, you can get:

- `equity_curve()` for strategy and buy-and-hold curves
- `kpis()` for the metrics reference
- `trades` for trade-by-trade details

## What The Report Tracks

The report reconstructs strategy equity by:

- starting from the initial balance
- adding realized PnL when trades close
- marking open trades to market between entry and exit

It also builds a buy-and-hold benchmark using the first and last close in the dataset.

## Mental Model

The easiest way to think about the engine is:

```text
load data -> build signal columns -> loop over bars -> fill pending orders
-> manage intrabar risk -> queue new orders -> close remaining exposure -> summarize
```

That sequence is the backbone of how ZStar turns a strategy into a completed backtest.
