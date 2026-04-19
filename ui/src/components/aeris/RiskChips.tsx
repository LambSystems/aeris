import { AlertTriangle } from "lucide-react";
import { formatRiskFlag } from "@/lib/format";
import { cn } from "@/lib/utils";

interface RiskChipsProps {
  flags: string[];
  className?: string;
}

export function RiskChips({ flags, className }: RiskChipsProps) {
  if (!flags?.length) {
    return (
      <p className="text-xs text-muted-foreground">
        No active environmental risks.
      </p>
    );
  }
  return (
    <div className={cn("flex flex-wrap gap-1.5", className)}>
      {flags.map((flag) => (
        <span
          key={flag}
          className="inline-flex items-center gap-1.5 rounded-full border border-warning/30 bg-warning-soft px-2.5 py-1 text-xs font-medium text-warning-foreground"
        >
          <AlertTriangle className="h-3 w-3" strokeWidth={2.25} />
          {formatRiskFlag(flag)}
        </span>
      ))}
    </div>
  );
}
