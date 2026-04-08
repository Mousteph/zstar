import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  SECTION_TITLE_CLASS_NAME,
  TABLE_HEADER_ROW_CLASS_NAME,
} from "@/features/backtest/constants";
import {
  formatDateTime,
  formatCurrency,
  formatNumber,
  getTradePnlClassName,
  getTradeRowClassName,
  getTradeSideBadgeClassName,
} from "@/features/backtest/utils";
import type { Trade } from "@/types/backtest";

interface RecentTradesTableProps {
  readonly trades: Trade[];
}

export function RecentTradesTable({ trades }: RecentTradesTableProps) {
  const sortedTrades = [...trades].sort(
    (a, b) => new Date(b.exit_datetime).getTime() - new Date(a.exit_datetime).getTime(),
  );

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
              <TableHead className="h-11 py-2 text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">
                Entry Time
              </TableHead>
              <TableHead className="h-11 py-2 text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">
                Exit Time
              </TableHead>
              <TableHead className="h-11 py-2 text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">
                Symbol
              </TableHead>
              <TableHead className="h-11 py-2 text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">
                Side
              </TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">
                Size
              </TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">
                Entry
              </TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">
                Exit
              </TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">
                Fees
              </TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.16em] text-muted-foreground">
                Net PnL
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedTrades.map((trade, index) => (
              <TableRow key={trade.id} className={getTradeRowClassName(index)}>
                <TableCell className="py-3 text-[0.94rem] font-medium">{formatDateTime(trade.entry_datetime)}</TableCell>
                <TableCell className="py-3 text-[0.94rem]">{formatDateTime(trade.exit_datetime)}</TableCell>
                <TableCell className="py-3 text-[0.94rem]">{trade.symbol}</TableCell>
                <TableCell className="py-3">
                  <span className={getTradeSideBadgeClassName(trade.side)}>{trade.side}</span>
                </TableCell>
                <TableCell className="py-3 text-right text-[0.94rem]">{formatNumber(trade.size)}</TableCell>
                <TableCell className="py-3 text-right text-[0.94rem]">{formatCurrency(trade.entry_price)}</TableCell>
                <TableCell className="py-3 text-right text-[0.94rem]">{formatCurrency(trade.exit_price)}</TableCell>
                <TableCell className="py-3 text-right text-[0.94rem]">{formatCurrency(trade.total_fees)}</TableCell>
                <TableCell className={`${getTradePnlClassName(trade.net_pnl)} py-3 text-[0.94rem]`}>
                  {formatCurrency(trade.net_pnl)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </section>
  );
}
