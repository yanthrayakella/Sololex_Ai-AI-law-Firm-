type Props = { score: number; label?: string };

export function ComplianceRing({ score, label = "Compliance score" }: Props) {
  const clamped = Math.max(0, Math.min(100, score));
  const r = 52;
  const c = 2 * Math.PI * r;
  const p = (clamped / 100) * c;
  return (
    <div className="flex items-center gap-4">
      <svg width="100" height="100" viewBox="0 0 120 120" className="-rotate-90 shrink-0">
        <circle cx="60" cy="60" r={r} fill="none" stroke="#e2e8f0" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke="#2563eb"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${p} ${c}`}
        />
      </svg>
      <div>
        <div className="text-3xl font-bold text-slate-900">{clamped}%</div>
        <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {label}
        </div>
        {clamped < 85 && (
          <div className="mt-1 text-xs font-semibold text-amber-700">Action recommended</div>
        )}
        {clamped >= 85 && (
          <div className="mt-1 text-xs font-semibold text-emerald-700">Strong compliance</div>
        )}
      </div>
    </div>
  );
}
