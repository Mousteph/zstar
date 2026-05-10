"use client";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/atoms/Table";
import { SECTION_TITLE_CLASS_NAME, TABLE_HEADER_ROW_CLASS_NAME } from "@/features/backtest/constants";
import {
  formatCurrency,
  formatDateTime,
  formatNumber,
  getTradePnlClassName,
  getTradeRowClassName,
  getTradeSideBadgeClassName,
  sourceTimestampToUtcMilliseconds,
} from "@/features/backtest/utils";
import type { Trade } from "@/types/backtest";

interface RecentTradesTableProps {
  readonly trades: Trade[];
  readonly selectedTradeId: string | null;
  readonly onSelectedTradeIdChange: (tradeId: string | null) => void;
}

export function RecentTradesTable({
  trades,
  selectedTradeId,
  onSelectedTradeIdChange,
}: Readonly<RecentTradesTableProps>) {
  const sortedTrades = [...trades].sort(
    (a, b) =>
      (sourceTimestampToUtcMilliseconds(b.exit_datetime) ?? 0) -
      (sourceTimestampToUtcMilliseconds(a.exit_datetime) ?? 0),
  );

  const toggleSelectedTrade = (tradeId: string) => {
    onSelectedTradeIdChange(selectedTradeId === tradeId ? null : tradeId);
  };

  return (
    <section className="border-b border-border/80 px-2 pb-10 sm:px-4 lg:px-6">
      <div className="mb-5">
        <h3 className={SECTION_TITLE_CLASS_NAME}>Trades</h3>
      </div>
      {sortedTrades.length === 0 ? (
        <p className="text-sm text-muted-foreground">No trades yet. Run a backtest to see executions.</p>
      ) : null}
      {sortedTrades.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow className={TABLE_HEADER_ROW_CLASS_NAME}>
              <TableHead className="h-11 py-2 text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Entry Time</TableHead>
              <TableHead className="h-11 py-2 text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Exit Time</TableHead>
              <TableHead className="h-11 py-2 text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Symbol</TableHead>
              <TableHead className="h-11 py-2 text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Side</TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Size</TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Entry</TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Exit</TableHead>
              <TableHead className="h-11 py-2 text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Reason</TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Stop Loss</TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Take Profit</TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Fees</TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">Net PnL</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedTrades.map((trade, index) => {
              const isSelected = selectedTradeId === trade.id;

              return (
                <TableRow
                  key={trade.id}
                  data-state={isSelected ? "selected" : "idle"}
                  className={[
                    getTradeRowClassName(index),
                    "cursor-pointer",
                    isSelected ? "bg-emerald-500/10 ring-1 ring-emerald-400/40 hover:bg-emerald-500/15" : "",
                    selectedTradeId && !isSelected ? "opacity-45 hover:opacity-70" : "",
                  ].join(" ")}
                  onClick={() => toggleSelectedTrade(trade.id)}
                >
                  <TableCell className="py-3 text-[0.94rem] font-medium">
                    <button
                      type="button"
                      className="w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                      aria-pressed={isSelected}
                      title={isSelected ? "Show all trades on the chart" : "Show only this trade on the chart"}
                      onClick={(event) => {
                        event.stopPropagation();
                        toggleSelectedTrade(trade.id);
                      }}
                    >
                      {formatDateTime(trade.entry_datetime)}
                    </button>
                  </TableCell>
                  <TableCell className="py-3 text-[0.94rem]">{formatDateTime(trade.exit_datetime)}</TableCell>
                  <TableCell className="py-3 text-[0.94rem]">{trade.symbol}</TableCell>
                  <TableCell className="py-3">
                    <span className={getTradeSideBadgeClassName(trade.side)}>{trade.side}</span>
                  </TableCell>
                  <TableCell className="py-3 text-right text-[0.94rem]">{formatNumber(trade.size)}</TableCell>
                  <TableCell className="py-3 text-right text-[0.94rem]">{formatCurrency(trade.entry_price)}</TableCell>
                  <TableCell className="py-3 text-right text-[0.94rem]">{formatCurrency(trade.exit_price)}</TableCell>
                  <TableCell className="py-3 text-[0.94rem] capitalize">
                    {trade.exit_reason.replaceAll("_", " ")}
                  </TableCell>
                  <TableCell className="py-3 text-right text-[0.94rem]">
                    {trade.stop_loss_price === null ? "N/A" : formatCurrency(trade.stop_loss_price)}
                  </TableCell>
                  <TableCell className="py-3 text-right text-[0.94rem]">
                    {trade.take_profit_price === null ? "N/A" : formatCurrency(trade.take_profit_price)}
                  </TableCell>
                  <TableCell className="py-3 text-right text-[0.94rem]">{formatCurrency(trade.total_fees)}</TableCell>
                  <TableCell className={`${getTradePnlClassName(trade.net_pnl)} py-3 text-[0.94rem]`}>
                    {formatCurrency(trade.net_pnl)}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      ) : null}
    </section>
  );
}
