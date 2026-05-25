import { useCallback, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { SAMPLE_WORK_PERMIT } from "../data/sampleWorkPermit";
import { ComplianceRing } from "../components/ComplianceRing";
import { CHANGE_SUMMARY_ITEMS, mergeWorkPermitWithRegulations } from "../utils/mergeWorkPermit";
import { extractTextFromFile } from "../utils/extractFileText";
import { downloadGovernmentUpdatesPdf } from "../utils/generateGovernmentPdf";
import { downloadUpdatedWorkPermitPdf } from "../utils/generateUpdatedPdf";

const LAST_CHECK = "Today 08:00 AM";
const NEXT_CHECK = "Today 2:00 PM";

export default function JudgePresentationPage() {
  const [permitText, setPermitText] = useState<string>(SAMPLE_WORK_PERMIT);
  const [fileLabel, setFileLabel] = useState<string>("Sample work permit (loaded)");
  const [parseError, setParseError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);
  const [mergedText, setMergedText] = useState<string | null>(null);
  const [lastApplied, setLastApplied] = useState<string>("Never");

  const regulationsThisWeek = 3;
  const updatesThisMonth = 12;
  const totalMonitored = 127;

  const docRequiresUpdate = useMemo(() => {
    if (updateSuccess) return 0;
    return 1;
  }, [updateSuccess]);

  const pendingCount = useMemo(() => (updateSuccess ? 0 : 1), [updateSuccess]);
  const urgent = !updateSuccess;

  const complianceScore = useMemo(() => (updateSuccess ? 94 : 72), [updateSuccess]);

  const onDrop = useCallback(async (accepted: File[]) => {
    const file = accepted[0];
    if (!file) return;
    setParseError(null);
    setUpdateSuccess(false);
    setMergedText(null);
    setFileLabel(file.name);
    try {
      const text = await extractTextFromFile(file);
      if (!text.trim()) {
        setParseError("No text could be read from this file. Try TXT or use the sample.");
        return;
      }
      setPermitText(text);
    } catch (e) {
      setParseError(e instanceof Error ? e.message : "Could not read file");
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: 1,
    multiple: false,
  });

  const loadSample = () => {
    setPermitText(SAMPLE_WORK_PERMIT);
    setFileLabel("sample-work-permit.txt (embedded)");
    setParseError(null);
    setUpdateSuccess(false);
    setMergedText(null);
  };

  const runUpdate = () => {
    setParseError(null);
    setUpdating(true);
    setUpdateSuccess(false);
    setMergedText(null);
    window.setTimeout(() => {
      const when = new Date().toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
      const merged = mergeWorkPermitWithRegulations(permitText, when);
      setMergedText(merged);
      setLastApplied(when);
      setUpdateSuccess(true);
      setUpdating(false);
    }, 3000);
  };

  const downloadUpdated = () => {
    if (!mergedText) return;
    downloadUpdatedWorkPermitPdf(mergedText, "Updated-Work-Permit-March-2026.pdf");
  };

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Top header + status */}
      <header className="border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto max-w-6xl px-4 py-6">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">
            ComplyAI — Work Permit Intelligence
          </h1>
          <div className="mt-3 flex flex-col gap-2 text-sm text-slate-600 md:flex-row md:items-center md:justify-between md:text-base">
            <p>
              <span className="font-semibold text-slate-800">Last Check:</span> {LAST_CHECK}{" "}
              <span className="mx-2 text-slate-300">|</span>
              <span className="font-semibold text-blue-700">3 New Updates Available</span>
            </p>
            <p className="flex items-center gap-2 font-medium text-emerald-700">
              <span className="text-lg">✅</span> System Active | Monitoring 6 Government Sources
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8">
        {/* Compliance dashboard */}
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-md">
          <div className="border-b border-blue-100 bg-gradient-to-r from-blue-50 to-white px-6 py-4">
            <h2 className="flex items-center gap-2 text-lg font-bold text-slate-900">
              <span aria-hidden>📊</span> Your compliance dashboard
            </h2>
          </div>
          <div className="grid gap-6 p-6 md:grid-cols-[1fr_auto] md:items-center">
            <ul className="space-y-2 text-sm text-slate-700 md:text-base">
              <li>
                •{" "}
                <span className="font-semibold text-slate-900">
                  {regulationsThisWeek} Regulations Detected This Week
                </span>
              </li>
              <li className={docRequiresUpdate ? "font-semibold text-amber-800" : "text-emerald-800"}>
                • {docRequiresUpdate} Document Requires Immediate Update
              </li>
              <li>
                • Last Update Applied: <span className="font-medium">{lastApplied}</span>
              </li>
              <li className="flex flex-wrap items-center gap-2">
                • Compliance Score:{" "}
                <span className="font-bold text-blue-800">{complianceScore}%</span>
                {!updateSuccess && (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">
                    Action recommended
                  </span>
                )}
              </li>
              <li>
                • Next Scheduled Check: <span className="font-medium">{NEXT_CHECK}</span>
              </li>
              <li>
                • Total Regulations Monitored:{" "}
                <span className="font-semibold">{totalMonitored}</span>
              </li>
            </ul>
            <ComplianceRing score={complianceScore} />
          </div>
        </section>

        {/* Three main cards */}
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-md transition hover:shadow-lg">
            <div className="text-2xl" aria-hidden>
              📄
            </div>
            <h3 className="mt-2 text-sm font-bold uppercase tracking-wide text-blue-800">
              Latest updates
            </h3>
            <p className="mt-3 text-2xl font-bold text-slate-900">3 New Updates Today</p>
            <p className="mt-1 text-sm text-slate-600">View what changed</p>
            <button
              type="button"
              onClick={() => downloadGovernmentUpdatesPdf()}
              className="mt-auto w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow transition hover:bg-blue-500 active:scale-[0.98]"
            >
              Download Latest Updates (PDF)
            </button>
          </div>

          <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-md transition hover:shadow-lg">
            <div className="text-2xl" aria-hidden>
              📎
            </div>
            <h3 className="mt-2 text-sm font-bold uppercase tracking-wide text-blue-800">
              My work permit
            </h3>
            <p className="mt-3 min-h-[3rem] text-sm font-medium text-slate-800">
              {fileLabel ? (
                <>
                  <span className="text-emerald-700">✓</span> {fileLabel}
                </>
              ) : (
                "No file uploaded"
              )}
            </p>
            <p className="text-xs text-slate-500">PDF, DOCX, or TXT</p>
            <div
              {...getRootProps()}
              className={`mt-4 cursor-pointer rounded-xl border-2 border-dashed px-4 py-8 text-center text-sm transition ${
                isDragActive
                  ? "border-blue-500 bg-blue-50 text-blue-800"
                  : "border-slate-300 bg-slate-50 text-slate-600 hover:border-blue-400 hover:bg-blue-50/50"
              }`}
            >
              <input {...getInputProps()} />
              {isDragActive ? "Drop file here…" : "Drag & drop or click to upload"}
            </div>
            <button
              type="button"
              onClick={loadSample}
              className="mt-3 w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
            >
              Use sample work permit
            </button>
            {parseError && (
              <p className="mt-2 text-xs font-medium text-red-600">{parseError}</p>
            )}
          </div>

          <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-md transition hover:shadow-lg">
            <div className="text-2xl" aria-hidden>
              🔄
            </div>
            <h3 className="mt-2 text-sm font-bold uppercase tracking-wide text-blue-800">
              Update and download
            </h3>
            <p className="mt-3 text-sm text-slate-600">
              Apply all 3 new regulations to your permit text and export.
            </p>
            <button
              type="button"
              disabled={updating}
              onClick={runUpdate}
              className="mt-4 w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white shadow transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 active:scale-[0.98]"
            >
              {updating ? "Applying 3 new regulations…" : "Update My Work Permit"}
            </button>
            <button
              type="button"
              disabled={!updateSuccess || !mergedText}
              onClick={downloadUpdated}
              className="mt-3 w-full rounded-xl border-2 border-blue-600 bg-white px-4 py-3 text-sm font-semibold text-blue-700 transition hover:bg-blue-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400 active:scale-[0.98]"
            >
              Download Updated Work Permit
            </button>
            <div className="mt-4 min-h-[4rem] rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm">
              {updating && (
                <p className="animate-pulse font-medium text-blue-700">Applying 3 new regulations…</p>
              )}
              {!updating && updateSuccess && (
                <p className="font-semibold text-emerald-700">
                  Work Permit Updated Successfully!
                </p>
              )}
              {!updating && !updateSuccess && (
                <p className="text-slate-500">Status: Awaiting update</p>
              )}
            </div>
          </div>
        </div>

        {/* Change summary */}
        {updateSuccess && (
          <section className="rounded-2xl border border-emerald-200 bg-emerald-50/80 p-6 shadow-md">
            <h3 className="text-lg font-bold text-emerald-900">Change summary</h3>
            <ul className="mt-3 space-y-2 text-sm font-medium text-emerald-900 md:text-base">
              {CHANGE_SUMMARY_ITEMS.map((item) => (
                <li key={item}>✅ {item}</li>
              ))}
            </ul>
          </section>
        )}

        {/* Quick stats row */}
        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-md">
            <p className="text-sm font-semibold text-slate-500">🕒 Last check</p>
            <p className="mt-2 text-lg font-bold text-slate-900">{LAST_CHECK}</p>
            <p className="text-sm text-slate-600">Next: {NEXT_CHECK}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-md">
            <p className="text-sm font-semibold text-slate-500">📜 Updates found</p>
            <p className="mt-2 text-lg font-bold text-slate-900">{regulationsThisWeek} This Week</p>
            <p className="text-sm text-slate-600">{updatesThisMonth} This Month</p>
          </div>
          <div
            className={`rounded-xl border p-5 shadow-md ${
              urgent ? "border-amber-300 bg-amber-50" : "border-slate-200 bg-white"
            }`}
          >
            <p className="text-sm font-semibold text-slate-500">⚠ Pending</p>
            <p className="mt-2 text-lg font-bold text-slate-900">Actions: {pendingCount}</p>
            <p className={`text-sm font-semibold ${urgent ? "text-amber-800" : "text-emerald-700"}`}>
              Urgent: {urgent ? "Yes" : "No"}
            </p>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        Judge presentation build — runs entirely in the browser — sample data only
      </footer>
    </div>
  );
}
