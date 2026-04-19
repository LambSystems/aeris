import {
  Wind,
  Droplets,
  Gauge,
  CloudRain,
  Activity,
  MapPin,
  Loader2,
  Home,
  Trees,
  Sparkles,
} from "lucide-react";
import type {
  DetectedObject,
  FixedContextResponse,
  SustainabilityResponse,
} from "@/lib/types";
import { formatConfidence, formatNumber, formatObjectName } from "@/lib/format";
import { MetricTile } from "./MetricTile";
import { RiskChips } from "./RiskChips";
import { RecommendationCard } from "./RecommendationCard";
import { StatusChip } from "./StatusChip";

interface DecisionPanelProps {
  primaryObject: DetectedObject | null;
  context: FixedContextResponse | null;
  contextLoading: boolean;
  contextError: string | null;
  recommendation: SustainabilityResponse | null;
  recommendationLoading: boolean;
  recommendationUpdating: boolean;
  sceneMode: "indoor" | "outdoor";
}

export function DecisionPanel({
  primaryObject,
  context,
  contextLoading,
  contextError,
  recommendation,
  recommendationLoading,
  recommendationUpdating,
  sceneMode,
}: DecisionPanelProps) {
  const castnet = context?.castnet;
  const aq = context?.air_quality;
  const weather = context?.weather;
  const alert = context?.weather_alerts?.[0];
  const riskFlags = recommendation?.risk_flags ?? context?.risk_flags ?? [];

  return (
    <aside className="flex h-full flex-col gap-4">
      {/* 1. Current scan */}
      <Section
        title="Current scan"
        eyebrow={
          <StatusChip
            label={sceneMode === "indoor" ? "Indoor scan" : "Outdoor context active"}
            tone={sceneMode === "indoor" ? "muted" : "accent"}
            icon={sceneMode === "indoor" ? Home : Trees}
          />
        }
      >
        {primaryObject ? (
          <div className="flex items-baseline justify-between gap-3">
            <div>
              <p className="text-[10.5px] font-medium uppercase tracking-wider text-muted-foreground">
                Detected object
              </p>
              <p className="mt-0.5 text-2xl font-semibold leading-tight text-foreground">
                {formatObjectName(primaryObject.name)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-[10.5px] font-medium uppercase tracking-wider text-muted-foreground">
                Confidence
              </p>
              <p className="mt-0.5 text-2xl font-semibold tabular-nums text-foreground">
                {formatConfidence(primaryObject.confidence)}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4" strokeWidth={2} />
            Waiting for detection…
          </div>
        )}
      </Section>

      {/* 2. Recommendation */}
      <RecommendationCard
        action={recommendation?.action ?? null}
        reason={recommendation?.context ?? null}
        source={recommendation?.decision_source ?? null}
        loading={recommendationLoading && !recommendation}
        updating={recommendationUpdating}
        empty={!primaryObject && !recommendation}
      />

      {/* 3. Environmental context */}
      <Section
        title="Environmental context"
        eyebrow={
          castnet?.location ? (
            <StatusChip
              label={castnet.location}
              tone="accent"
              icon={MapPin}
            />
          ) : null
        }
      >
        {contextLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Gathering local environmental data…
          </div>
        ) : contextError ? (
          <p className="text-sm text-muted-foreground">
            Environmental context unavailable.
          </p>
        ) : (
          <div className="grid grid-cols-2 gap-2">
            <MetricTile
              label="Ozone"
              value={formatNumber(castnet?.ozone_ppb, 1)}
              unit="ppb"
              icon={Activity}
              emphasis={
                castnet?.ozone_ppb && castnet.ozone_ppb > 60
                  ? "warning"
                  : "neutral"
              }
            />
            <MetricTile
              label="Nitrate"
              value={formatNumber(castnet?.nitrate_ug_m3, 2)}
              unit="µg/m³"
              icon={Droplets}
              emphasis={
                castnet?.nitrate_ug_m3 && castnet.nitrate_ug_m3 > 2
                  ? "warning"
                  : "neutral"
              }
            />
            <MetricTile
              label="PM2.5"
              value={formatNumber(aq?.pm2_5_ug_m3, 1)}
              unit="µg/m³"
              icon={Gauge}
              emphasis={
                aq?.pm2_5_ug_m3 && aq.pm2_5_ug_m3 > 35 ? "warning" : "neutral"
              }
            />
            <MetricTile
              label="Wind"
              value={formatNumber(weather?.wind_speed_kmh, 0)}
              unit="km/h"
              icon={Wind}
            />
            {alert ? (
              <div className="col-span-2 flex items-start gap-2 rounded-md border border-warning/30 bg-warning-soft px-3 py-2 text-sm text-warning-foreground">
                <CloudRain className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={2.25} />
                <div>
                  <p className="font-medium">
                    {alert.event ?? "Weather alert"}
                  </p>
                  {alert.headline ? (
                    <p className="text-xs opacity-80">{alert.headline}</p>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </Section>

      {/* 4. Risk signals */}
      <Section title="Risk signals">
        <RiskChips flags={riskFlags} />
      </Section>

      {/* 5. System footer */}
      <SystemFooter context={context} />
    </aside>
  );
}

function Section({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border bg-card p-4">
      <header className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          {title}
        </h2>
        {eyebrow}
      </header>
      {children}
    </section>
  );
}

function SystemFooter({ context }: { context: FixedContextResponse | null }) {
  const sources = context?.source_status ?? {};
  const entries = Object.entries(sources);
  if (entries.length === 0) {
    return (
      <p className="px-1 text-[10.5px] text-muted-foreground">
        Aeris · environmental sustainability scanner
      </p>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-1 text-[10.5px] text-muted-foreground">
      <span className="font-medium uppercase tracking-wider">System</span>
      {entries.map(([k, v]) => (
        <span key={k} className="inline-flex items-center gap-1">
          <span
            className={
              v === "ok"
                ? "h-1 w-1 rounded-full bg-primary"
                : "h-1 w-1 rounded-full bg-warning"
            }
          />
          {k}
        </span>
      ))}
    </div>
  );
}
