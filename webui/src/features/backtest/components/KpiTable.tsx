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
import type { KpiRow } from "@/types/backtest";

interface KpiTableProps {
  readonly rows: KpiRow[];
}

export function KpiTable({ rows }: KpiTableProps) {
  return (
    <section className="border-b border-border/80 px-2 pb-10 sm:px-4 lg:px-6">
      <div className="mb-5">
        <h3 className={SECTION_TITLE_CLASS_NAME}>All KPIs</h3>
      </div>
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">Run a backtest to populate KPI metrics.</p>
      ) : null}
      {rows.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow className={TABLE_HEADER_ROW_CLASS_NAME}>
              <TableHead className="h-11 py-2 text-[0.74rem] uppercase tracking-[0.18em] text-muted-foreground">
                Metric
              </TableHead>
              <TableHead className="h-11 py-2 text-right text-[0.74rem] uppercase tracking-[0.18em] text-muted-foreground">
                Value
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.key} className="border-border/80">
                <TableCell className="py-3 text-[0.98rem] text-foreground/90">{row.label}</TableCell>
                <TableCell className="py-3 text-right text-[0.98rem] font-medium text-foreground">
                  {row.value}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </section>
  );
}
