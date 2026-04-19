import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface MetricTileProps {
  label: string;
  value: string;
  unit?: string;
  icon?: LucideIcon;
  emphasis?: "neutral" | "warning" | "accent";
  className?: string;
}

const emphasisRing: Record<NonNullable<MetricTileProps["emphasis"]>, string> = {
  neutral: "border-border",
  warning: "border-warning/40 bg-warning-soft/40",
  accent: "border-accent/30 bg-accent-soft/40",
};

export function MetricTile({
  label,
  value,
  unit,
  icon: Icon,
  emphasis = "neutral",
  className,
}: MetricTileProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-1 rounded-md border bg-card px-3 py-2.5",
        emphasisRing[emphasis],
        className,
      )}
    >
      <div className="flex items-center gap-1.5 text-[10.5px] font-medium uppercase tracking-wider text-muted-foreground">
        {Icon ? <Icon className="h-3 w-3" strokeWidth={2.25} /> : null}
        <span>{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-lg font-semibold tabular-nums text-foreground">
          {value}
        </span>
        {unit ? (
          <span className="text-xs text-muted-foreground">{unit}</span>
        ) : null}
      </div>
    </div>
  );
}
