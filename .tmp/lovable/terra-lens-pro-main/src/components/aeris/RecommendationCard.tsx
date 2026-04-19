import { Recycle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface RecommendationCardProps {
  action: string | null;
  reason?: string | null;
  loading?: boolean;
  updating?: boolean;
  empty?: boolean;
}

export function RecommendationCard({
  action,
  reason,
  loading,
  updating,
  empty,
}: RecommendationCardProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-lg border bg-gradient-to-br from-primary-soft to-card p-4",
        "border-primary/20",
      )}
    >
      <div className="flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/15 text-primary">
          <Recycle className="h-4 w-4" strokeWidth={2.25} />
        </div>
        <span className="text-[10.5px] font-semibold uppercase tracking-wider text-primary">
          Recommended action
        </span>
        {updating ? (
          <span className="ml-auto inline-flex items-center gap-1 text-[10.5px] text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin" />
            Updating
          </span>
        ) : null}
      </div>

      <div className="mt-3 min-h-[3.5rem]">
        {loading ? (
          <div className="space-y-2">
            <div className="h-5 w-2/3 animate-pulse rounded bg-muted" />
            <div className="h-3 w-full animate-pulse rounded bg-muted" />
          </div>
        ) : empty || !action ? (
          <p className="text-sm text-muted-foreground">
            Point the camera at an item to receive a sustainability action.
          </p>
        ) : (
          <div className="animate-fade-in">
            <p className="text-balance text-lg font-semibold leading-snug text-foreground">
              {action}
            </p>
            {reason ? (
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                {reason}
              </p>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
