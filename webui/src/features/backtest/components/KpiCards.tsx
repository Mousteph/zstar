import { getKpiToneStyles } from "@/features/backtest/utils";
import { cn } from "@/lib/utils";
import type { KpiMetric } from "@/types/backtest";

interface KpiCardsProps {
  readonly metrics: KpiMetric[];
}

export function KpiCards({ metrics }: KpiCardsProps) {
  if (metrics.length === 0) {
    return (
      <section className="border-b border-border/80 px-2 pb-9 sm:px-4 lg:px-6">
        <p className="text-sm text-muted-foreground">Run a backtest to populate the headline KPIs.</p>
      </section>
    );
  }

  return (
    <section className="border-b border-border/80 px-2 pb-10 sm:px-4 lg:px-6">
      <div className="mx-auto grid w-full max-w-[1120px] grid-cols-1 justify-items-center gap-x-16 gap-y-14 md:grid-cols-2 xl:grid-cols-3">
        {metrics.map((metric) => {
          const tone = getKpiToneStyles(metric.tone);
          const valueClassName = tone.valueClassName || tone.iconClassName;

          return (
            <article key={metric.id} className="w-full max-w-[22rem] space-y-4">
              <p className={cn("text-5xl font-semibold leading-none tracking-[-0.03em] sm:text-6xl", valueClassName)}>
                {metric.value}
              </p>
              <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                {metric.label}
              </h3>
              <p className="max-w-[28ch] text-sm leading-relaxed text-muted-foreground">{metric.description}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
