import { useEffect, useMemo, useState } from "react";
import { Activity, Camera, Database, RefreshCcw, ShieldCheck, Sparkles } from "lucide-react";
import { analyzeScene, getAnalysisJob, runDemo } from "./api";
import type { ActionRecommendation, DemoRunResponse, SceneObject } from "./types/aeris";

const actionLabels: Record<ActionRecommendation["action"], string> = {
  protect_first: "Protect first",
  move_to_storage: "Move to storage",
  cover_if_time_allows: "Cover if time allows",
  low_priority: "Low priority",
};

function App() {
  const [demo, setDemo] = useState<DemoRunResponse | null>(null);
  const [status, setStatus] = useState<"ready" | "scanning" | "complete">("ready");
  const [analysisStatus, setAnalysisStatus] = useState<"idle" | "reasoning" | "complete" | "failed">("idle");
  const [decisionSource, setDecisionSource] = useState<string>("fallback_policy");
  const [scene, setScene] = useState<"demo" | "after_move">("demo");

  useEffect(() => {
    void loadDemo("demo");
  }, []);

  async function loadDemo(nextScene: "demo" | "after_move") {
    setStatus("scanning");
    setAnalysisStatus("idle");
    setDecisionSource("fallback_policy");
    const response = await runDemo(nextScene);
    setDemo(response);
    setScene(nextScene);
    setStatus("complete");
    void startAgentAnalysis(response);
  }

  async function startAgentAnalysis(response: DemoRunResponse) {
    setAnalysisStatus("reasoning");
    try {
      const job = await analyzeScene({
        fixed_context: response.fixed_context,
        dynamic_context: response.dynamic_context,
        provider: "gemini",
      });

      const completed = await waitForAnalysis(job.job_id);
      if (!completed.recommendations) {
        throw new Error("Analysis completed without recommendations.");
      }

      setDemo({
        ...response,
        recommendations: completed.recommendations,
      });
      setDecisionSource(completed.recommendations.decision_source);
      setAnalysisStatus("complete");
    } catch (error) {
      console.warn("Keeping fallback recommendation because async agent analysis failed.", error);
      setAnalysisStatus("failed");
      setDecisionSource("fallback_policy");
    }
  }

  async function waitForAnalysis(jobId: string) {
    for (let attempt = 0; attempt < 12; attempt += 1) {
      const job = await getAnalysisJob(jobId);
      if (job.status === "complete" || job.status === "failed") {
        return job;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 750));
    }

    throw new Error("Analysis timed out.");
  }

  const topAction = demo?.recommendations.actions[0];
  const detectedObjects = demo?.dynamic_context.objects ?? [];
  const sourceLabel = demo?.dynamic_context.source.replaceAll("_", " ") ?? "waiting";

  return (
    <main className="app-shell">
      <section className="hero-band">
        <div>
          <p className="eyebrow">HackAugie sustainability demo</p>
          <h1>Aeris</h1>
          <p className="subtitle">Pollution-aware scene analyzer for outdoor resource protection.</p>
        </div>
        <div className="system-status">
          <span className={`status-dot ${status}`} />
          {status === "scanning" ? "Analyzing visible resources" : "CASTNET context loaded"}
        </div>
      </section>

      <section className="workspace-grid">
        <section className="scene-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Dynamic context</p>
              <h2>Scene Scan</h2>
            </div>
            <span className="source-pill">{sourceLabel}</span>
          </div>

          <SceneCanvas objects={detectedObjects} topTarget={topAction?.target} />

          <div className="control-row">
            <button onClick={() => loadDemo("demo")}>
              <Camera size={18} />
              Scan Scene
            </button>
            <button className="secondary" onClick={() => loadDemo("demo")}>
              <Database size={18} />
              Use Demo Frame
            </button>
            <button className="secondary" onClick={() => loadDemo(scene === "demo" ? "after_move" : "demo")}>
              <RefreshCcw size={18} />
              Rescan
            </button>
          </div>
        </section>

        <aside className="decision-stack">
          <ContextPanel demo={demo} />
          <ActionsPanel actions={demo?.recommendations.actions ?? []} />
          <ExplanationPanel
            explanation={demo?.recommendations.explanation}
            insights={demo?.recommendations.missing_insights ?? []}
            status={analysisStatus}
            provider={decisionSource}
          />
        </aside>
      </section>
    </main>
  );
}

function SceneCanvas({ objects, topTarget }: { objects: SceneObject[]; topTarget?: string }) {
  const labels = useMemo(() => objects.filter((object) => object.bbox), [objects]);

  return (
    <div className="scene-canvas" aria-label="Detected outdoor resource scene">
      <div className="scan-gradient" />
      <div className="table-plane" />
      <div className="scan-line" />
      {labels.map((object) => (
        <div
          className={`bbox ${object.name === topTarget ? "priority" : ""}`}
          key={object.name}
          style={{
            left: `${(object.bbox!.x / 920) * 100}%`,
            top: `${(object.bbox!.y / 460) * 100}%`,
            width: `${(object.bbox!.width / 920) * 100}%`,
            height: `${(object.bbox!.height / 460) * 100}%`,
          }}
        >
          <span>
            {formatName(object.name)} {(object.confidence * 100).toFixed(0)}%
          </span>
        </div>
      ))}
      {labels.length === 0 && <p className="empty-state">Ready to scan the outdoor setup.</p>}
    </div>
  );
}

function ContextPanel({ demo }: { demo: DemoRunResponse | null }) {
  const context = demo?.fixed_context;

  return (
    <section className="info-panel context-panel">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">Fixed context</p>
          <h2>CASTNET Profile</h2>
        </div>
        <Database size={20} />
      </div>
      <p className="location">{context?.location ?? "Outdoor Garden Demo"}</p>
      <div className="metric-grid">
        <Metric label="Ozone Risk" value={context?.pollution_profile.ozone_risk ?? "high"} tone="alert" />
        <Metric label="Deposition Risk" value={context?.pollution_profile.deposition_risk ?? "medium"} tone="steady" />
      </div>
      <div className="mode-card">
        <span>Active Mode</span>
        <strong>{formatName(context?.risk_mode ?? "protect_plants_and_sensitive_equipment")}</strong>
      </div>
    </section>
  );
}

function ActionsPanel({ actions }: { actions: ActionRecommendation[] }) {
  return (
    <section className="info-panel actions-panel">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">Agentic decision</p>
          <h2>Latest Recommendation</h2>
        </div>
        <ShieldCheck size={20} />
      </div>
      <div className="action-list">
        {actions.slice(0, 4).map((action) => (
          <article className="action-item" key={`${action.rank}-${action.target}`}>
            <div className="rank">{action.rank}</div>
            <div>
              <strong>
                {actionLabels[action.action]}: {formatName(action.target)}
              </strong>
              <p>{action.reason}</p>
              <span className="score">Score {action.score.toFixed(2)}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ExplanationPanel({
  explanation,
  insights,
  status,
  provider,
}: {
  explanation?: string;
  insights: string[];
  status: "idle" | "reasoning" | "complete" | "failed";
  provider: string;
}) {
  return (
    <section className="info-panel explanation-panel">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">Agent reasoning</p>
          <h2>Recommendation Rationale</h2>
        </div>
        <Sparkles size={20} />
      </div>
      <div className={`explain-state ${status}`}>
        {status === "reasoning" && "Fallback visible. Agent is reasoning over latest scene..."}
        {status === "complete" && `Recommendation updated by ${provider}.`}
        {status === "failed" && "Fallback recommendation shown. Agent path unavailable."}
        {status === "idle" && "Latest recommendation ready."}
      </div>
      <p>{explanation ?? "Recommendations generated from environmental context and detected objects."}</p>
      {insights.length > 0 && (
        <div className="insight">
          <Activity size={16} />
          {insights[0]}
        </div>
      )}
    </section>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone: "alert" | "steady" }) {
  return (
    <div className={`metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatName(value: string) {
  return value.replaceAll("_", " ");
}

export default App;
