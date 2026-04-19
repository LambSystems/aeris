import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

type Tone = "neutral" | "primary" | "accent" | "warning" | "muted";

interface StatusChipProps {
  label: string;
  tone?: Tone;
  icon?: LucideIcon;
  pulse?: boolean;
  className?: string;
}

const toneStyles: Record<Tone, string> = {
  neutral: "bg-card text-foreground border-border",
  primary: "bg-primary-soft text-primary border-primary/20",
  accent: "bg-accent-soft text-accent border-accent/20",
  warning: "bg-warning-soft text-warning-foreground border-warning/30",
  muted: "bg-muted text-muted-foreground border-transparent",
};

const dotStyles: Record<Tone, string> = {
  neutral: "bg-muted-foreground",
  primary: "bg-primary",
  accent: "bg-accent",
  warning: "bg-warning",
  muted: "bg-muted-foreground/60",
};

export function StatusChip({
  label,
  tone = "neutral",
  icon: Icon,
  pulse,
  className,
}: StatusChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        toneStyles[tone],
        className,
      )}
    >
      {Icon ? (
        <Icon className="h-3.5 w-3.5" strokeWidth={2.25} />
      ) : (
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            dotStyles[tone],
            pulse && "animate-pulse-soft",
          )}
        />
      )}
      <span className="leading-none">{label}</span>
    </span>
  );
}
