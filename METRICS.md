# Backtesting Metrics Reference

## Overview

ZStar reports strategy, trade, and buy-and-hold metrics from a completed backtest. Strategy equity is reconstructed by starting with `initial_balance`, realizing each closed trade's `net_pnl` at its exit timestamp, and marking open trades to the current close price between entry and exit. Buy-and-hold equity assumes the full initial balance is invested at the very first bar's close and held through the final close; if that close is non-positive, no buy-and-hold curve is produced.

All percentage return and drawdown values are expressed in percent points, not decimals. For example, `12.5` means 12.5%.

---

## Individual Metrics

### Initial Balance

- **What It Means**: Starting account value supplied to the backtest.
- **Formula**: $$B_0$$
- **Implementation**: `kpis()` pass-through field `initial_balance`.
- **Interpretation**: Higher values only change the account scale; they do not imply better strategy quality.
- **Example**: If a backtest starts with `$10,000`, `initial_balance = 10000`.
- **Edge Cases**: If this is zero, percentage returns are undefined and the code returns `0.0` for return percentages.

### Final Balance

- **What It Means**: Ending account value after all simulated trades are closed.
- **Formula**: $$B_T$$
- **Implementation**: `kpis()` pass-through field `final_balance`.
- **Interpretation**: Must be compared with initial balance and risk; a higher final balance with extreme drawdown may still be unattractive.
- **Example**: Starting at `$10,000` and ending at `$10,800` gives `final_balance = 10800`.
- **Edge Cases**: Can be below the initial balance and can be negative if losses exceed starting capital.

### Net PnL

- **What It Means**: Absolute profit or loss over the full backtest.
- **Formula**: $$B_T - B_0$$
- **Implementation**: `_compute_net_pnl()`.
- **Interpretation**: Positive is profitable; negative is losing. It does not normalize for account size.
- **Example**: `$10,800 - $10,000 = $800`.
- **Edge Cases**: Negative values are valid and indicate losses.

### Total Return %

- **What It Means**: Strategy return normalized by starting capital.
- **Formula**: $$\frac{B_T - B_0}{B_0} \times 100$$
- **Implementation**: `_compute_return_pct(final_value)`.
- **Interpretation**: Higher is better, but should be read with drawdown and Sharpe ratio.
- **Example**: `($10,800 - $10,000) / $10,000 * 100 = 8%`.
- **Edge Cases**: Returns `0.0` when `initial_balance` is zero.

### Total Trades

- **What It Means**: Number of closed trades included in the report.
- **Formula**: $$N$$
- **Implementation**: `_compute_total_trades()`.
- **Interpretation**: Very low counts make win rate, average trade PnL, and Sharpe less statistically useful.
- **Example**: Ten closed trades gives `total_trades = 10`.
- **Edge Cases**: Returns `0` when no trades close.

### Total Fees

- **What It Means**: Total trading fees paid across all closed trades.
- **Formula**: $$\sum_{i=1}^{N} (entry\_fee_i + exit\_fee_i)$$
- **Implementation**: `_compute_total_fees()`.
- **Interpretation**: High fees relative to gross profit can turn a viable raw strategy into a losing net strategy.
- **Example**: Fees of `$2`, `$3`, and `$5` total `$10`.
- **Edge Cases**: Returns `0.0` when there are no trades.

### Gross Profit

- **What It Means**: Sum of all positive net trade PnL values.
- **Formula**: $$\sum_{i=1}^{N} \max(pnl_i, 0)$$
- **Implementation**: `_compute_gross_profit(wins)`.
- **Interpretation**: Measures winning dollars before offsetting losing trades.
- **Example**: Trade PnLs `[50, -20, 30]` produce gross profit `$80`.
- **Edge Cases**: Returns `0.0` when there are no winning trades.

### Gross Loss

- **What It Means**: Absolute sum of all negative net trade PnL values.
- **Formula**: $$\left|\sum_{i=1}^{N} \min(pnl_i, 0)\right|$$
- **Implementation**: `_compute_gross_loss(losses)`.
- **Interpretation**: Reported as a positive loss magnitude for ratio calculations.
- **Example**: Trade PnLs `[50, -20, 30]` produce gross loss `$20`.
- **Edge Cases**: Returns `0.0` when there are no losing trades.

### Win Rate %

- **What It Means**: Percentage of trades with positive net PnL.
- **Formula**: $$\frac{\#(pnl_i > 0)}{N} \times 100$$
- **Implementation**: `_compute_win_rate_pct(wins, total_trades)`.
- **Interpretation**: Above 50% is often comfortable, but profitable systems can have lower win rates if average wins are large.
- **Example**: Two winners out of three trades gives `66.67%`.
- **Edge Cases**: Returns `0.0` when there are no trades. Breakeven trades are not wins.

### Average Trade PnL

- **What It Means**: Mean net PnL per closed trade.
- **Formula**: $$\frac{1}{N}\sum_{i=1}^{N} pnl_i$$
- **Implementation**: `_compute_avg_trade_pnl(pnls)`.
- **Interpretation**: Positive values indicate average profitability per trade.
- **Example**: `[50, -20, 30]` averages to `$20`.
- **Edge Cases**: Returns `0.0` when there are no trades.

### Average Win

- **What It Means**: Mean net PnL among winning trades only.
- **Formula**: $$mean(pnl_i \mid pnl_i > 0)$$
- **Implementation**: `_compute_avg_win(wins)`.
- **Interpretation**: Should be compared with the magnitude of average loss.
- **Example**: Winning trades `[50, 30]` average to `$40`.
- **Edge Cases**: Returns `0.0` when there are no winning trades.

### Average Loss

- **What It Means**: Mean net PnL among losing trades only.
- **Formula**: $$mean(pnl_i \mid pnl_i < 0)$$
- **Implementation**: `_compute_avg_loss(losses)`.
- **Interpretation**: More negative values indicate larger losing trades.
- **Example**: Losing trades `[-20, -10]` average to `-$15`.
- **Edge Cases**: Returns `0.0` when there are no losing trades. The value is negative by design.

### Profit Factor

- **What It Means**: Gross profit earned per dollar of gross loss.
- **Formula**: $$\frac{gross\_profit}{gross\_loss}$$
- **Implementation**: `_compute_profit_factor(gross_profit, gross_loss)`.
- **Interpretation**: Values above `1.0` are profitable before considering capital efficiency. `1.5` to `2.0` is generally healthy.
- **Example**: Gross profit `$80` and gross loss `$20` gives `4.0`.
- **Edge Cases**: Returns `inf` when there is profit and no loss. Returns `NaN` when both gross profit and gross loss are zero.

### Maximum Drawdown %

- **What It Means**: Worst percentage decline from a prior strategy equity peak.
- **Formula**: $$\min_t \left(\frac{E_t}{\max_{s \le t} E_s} - 1\right) \times 100$$
- **Implementation**: `_compute_max_drawdown_pct(equity_curve)`.
- **Interpretation**: Values closer to `0` are better. A value of `-25` means equity fell 25% from a prior peak.
- **Example**: Equity `[1000, 1100, 900, 1200]` has drawdown `(900 / 1100 - 1) * 100 = -18.18%`.
- **Edge Cases**: Returns `0.0` for empty curves and ignores non-positive rolling peaks to avoid division by zero.

### Sharpe Ratio

- **What It Means**: Annualized excess return per unit of return volatility.
- **Formula**: $$\frac{mean(r_t - r_{f,period})}{std(r_t)} \times \sqrt{periods\_per\_year}$$
- **Implementation**: `_compute_sharpe_ratio(strategy_returns)`.
- **Interpretation**: Above `1.0` is often acceptable, above `2.0` is strong, and above `3.0` is exceptional.
- **Example**: Mean daily return `0.10%`, daily risk-free rate `0.01%`, daily volatility `1.0%`: `(0.001 - 0.0001) / 0.01 * sqrt(252) = 1.43`.
- **Edge Cases**: Returns `NaN` when there are fewer than two returns or zero volatility. `risk_free_rate` is an annual decimal, defaulting to `0.0`.

### Best Trade

- **What It Means**: Largest net PnL of any closed trade.
- **Formula**: $$\max_i pnl_i$$
- **Implementation**: `_compute_best_trade(pnls)`.
- **Interpretation**: Helps identify upside outliers.
- **Example**: `[50, -20, 30]` gives best trade `$50`.
- **Edge Cases**: Returns `0.0` when there are no trades.

### Worst Trade

- **What It Means**: Smallest net PnL of any closed trade.
- **Formula**: $$\min_i pnl_i$$
- **Implementation**: `_compute_worst_trade(pnls)`.
- **Interpretation**: Helps identify downside outliers and tail risk.
- **Example**: `[50, -20, 30]` gives worst trade `-$20`.
- **Edge Cases**: Returns `0.0` when there are no trades.

### Median Trade

- **What It Means**: Middle net PnL value across closed trades.
- **Formula**: $$median(pnl_i)$$
- **Implementation**: `_compute_median_trade(pnls)`.
- **Interpretation**: Less sensitive to outlier trades than average trade PnL.
- **Example**: `[50, -20, 30]` gives median trade `$30`.
- **Edge Cases**: Returns `0.0` when there are no trades.

### Average Trade Duration Minutes

- **What It Means**: Average elapsed time between trade entry and exit.
- **Formula**: $$mean\left(\frac{exit\_datetime_i - entry\_datetime_i}{60\ seconds}\right)$$
- **Implementation**: `_compute_avg_trade_duration_minutes()`.
- **Interpretation**: Useful for distinguishing intraday, swing, and longer-horizon behavior.
- **Example**: Trade durations `[60, 120, 30]` average to `70` minutes.
- **Edge Cases**: Returns `0.0` when there are no trades.

### Buy-and-Hold Final Balance

- **What It Means**: Ending value of investing the full initial balance at the first close and holding to the final close.
- **Formula**: $$close_T \times \frac{B_0}{close_0}$$
- **Implementation**: `_compute_buy_and_hold_final_balance(buy_and_hold_curve)`.
- **Interpretation**: Baseline account value for passive exposure to the same asset.
- **Example**: `$1,000` invested at `$100`, final close `$120`, final balance `$1,200`.
- **Edge Cases**: Returns `initial_balance` if market data is empty or the first close is non-positive.

### Buy-and-Hold Return %

- **What It Means**: Buy-and-hold return normalized by starting capital.
- **Formula**: $$\frac{buy\_hold_T - B_0}{B_0} \times 100$$
- **Implementation**: `_compute_buy_and_hold_return_pct(buy_and_hold_final)`.
- **Interpretation**: Strategy total return should be compared against this baseline.
- **Example**: `$1,200` final value from `$1,000` gives `20%`.
- **Edge Cases**: Returns `0.0` when `initial_balance` is zero.

### Buy-and-Hold Maximum Drawdown %

- **What It Means**: Worst percentage decline from a prior buy-and-hold equity peak.
- **Formula**: $$\min_t \left(\frac{BH_t}{\max_{s \le t} BH_s} - 1\right) \times 100$$
- **Implementation**: `_compute_buy_and_hold_max_drawdown_pct(buy_and_hold_curve)`.
- **Interpretation**: Shows passive asset risk over the same backtest window.
- **Example**: Buy-and-hold equity `[1000, 1100, 900, 1200]` gives `-18.18%`.
- **Edge Cases**: Returns `0.0` for empty or non-positive buy-and-hold curves.

### Return Difference vs Buy-and-Hold %

- **What It Means**: Strategy total return minus buy-and-hold total return.
- **Formula**: $$strategy\_return\_\% - buy\_hold\_return\_\%$$
- **Implementation**: `_compute_return_diff_vs_buy_and_hold_pct(strategy_return_pct, buy_and_hold_return_pct)`.
- **Interpretation**: Positive values mean the strategy outperformed passive exposure.
- **Example**: Strategy return `6%` and buy-and-hold return `20%` gives `-14%`.
- **Edge Cases**: No division occurs; both inputs are already percentages.

---

## Quick Reference Table

| Metric | Formula | Good Range | Implementation |
|--------|---------|------------|----------------|
| Net PnL | $$B_T - B_0$$ | Positive | `_compute_net_pnl()` |
| Total Return % | $$((B_T - B_0) / B_0) \times 100$$ | Strategy-dependent; positive and above benchmark | `_compute_return_pct()` |
| Total Trades | $$N$$ | Enough observations for the strategy horizon | `_compute_total_trades()` |
| Total Fees | $$\sum fees_i$$ | Low relative to gross profit | `_compute_total_fees()` |
| Gross Profit | $$\sum \max(pnl_i, 0)$$ | Positive and growing | `_compute_gross_profit()` |
| Gross Loss | $$|\sum \min(pnl_i, 0)|$$ | Controlled relative to gross profit | `_compute_gross_loss()` |
| Win Rate % | $$wins / N \times 100$$ | Often above 50%, but context-dependent | `_compute_win_rate_pct()` |
| Average Trade PnL | $$mean(pnl_i)$$ | Positive | `_compute_avg_trade_pnl()` |
| Average Win | $$mean(pnl_i \mid pnl_i > 0)$$ | Larger than absolute average loss | `_compute_avg_win()` |
| Average Loss | $$mean(pnl_i \mid pnl_i < 0)$$ | Less negative is better | `_compute_avg_loss()` |
| Profit Factor | $$gross\_profit / gross\_loss$$ | `> 1.0` profitable, `> 1.5` healthy, `> 2.0` strong | `_compute_profit_factor()` |
| Maximum Drawdown % | $$min(E_t / peak_t - 1) \times 100$$ | Closer to `0`; often above `-20%` for controlled risk | `_compute_max_drawdown_pct()` |
| Sharpe Ratio | $$mean(r_t-r_f) / std(r_t) \times \sqrt{periods}$$ | `> 1` acceptable, `> 2` strong, `> 3` exceptional | `_compute_sharpe_ratio()` |
| Best Trade | $$max(pnl_i)$$ | Positive, but not the only source of returns | `_compute_best_trade()` |
| Worst Trade | $$min(pnl_i)$$ | Limited downside outliers | `_compute_worst_trade()` |
| Median Trade | $$median(pnl_i)$$ | Positive | `_compute_median_trade()` |
| Avg Duration | $$mean(duration_i)$$ | Matches intended holding period | `_compute_avg_trade_duration_minutes()` |
| Buy-and-Hold Final | $$close_T \times B_0 / close_0$$ | Benchmark only | `_compute_buy_and_hold_final_balance()` |
| Buy-and-Hold Return % | $$((BH_T - B_0) / B_0) \times 100$$ | Benchmark only | `_compute_buy_and_hold_return_pct()` |
| Buy-and-Hold MDD % | $$min(BH_t / BH\_peak_t - 1) \times 100$$ | Closer to `0` | `_compute_buy_and_hold_max_drawdown_pct()` |
| Return Diff vs B&H % | $$strategy\_return - buy\_hold\_return$$ | Positive | `_compute_return_diff_vs_buy_and_hold_pct()` |

---

## Assumptions & Limitations

- `risk_free_rate` is an annual decimal return, such as `0.04` for 4%, and defaults to `0.0`.
- Sharpe ratio annualization assumes 252 trading days per year and 390 trading minutes per regular trading day.
- Supported interval suffixes for annualization are `d`, `h`, and `m`; unknown formats fall back to daily annualization.
- Strategy equity marks open trades to the current bar close between `entry_datetime` and `exit_datetime`.
- Open-trade equity includes realized PnL from already closed trades, current raw unrealized PnL, and the open trade's entry fee. The exit fee is applied when the trade closes.
- Buy-and-hold uses close prices and assumes all starting capital is invested at the first close.
- Buy-and-hold does not include fees, slippage, dividends, borrow costs, funding, or cash interest.
- Profit factor is `inf` for a profitable strategy with no losing trades and `NaN` when there is no profit and no loss.
- Breakeven trades with `net_pnl == 0` are counted as trades, but not as wins or losses.
- Average loss is intentionally negative, while gross loss is intentionally positive.
- Percentage returns return `0.0` when `initial_balance == 0` because the mathematical value is undefined.

---

## Common Mistakes

- Treating high win rate as proof of profitability. A low win rate can work with large winners; a high win rate can fail with large losses.
- Reading profit factor without sample size. A profit factor of `inf` over two winning trades is not robust evidence.
- Comparing net PnL across backtests with different starting balances instead of comparing return percentages and risk.
- Ignoring drawdown. A strategy can show strong total return while taking unacceptable interim losses.
- Treating Sharpe ratio as reliable when there are few trades or mostly flat equity returns.
- Forgetting that strategy equity is marked to close prices while a trade is open, not to intrabar highs or lows.
- Comparing strategy returns to buy-and-hold without checking whether the strategy used less capital or carried lower drawdown.
