# ComplyAI — Work Permit Intelligence (Judge Presentation)

**Frontend-only** demo: no backend, no login. All PDFs and document updates run in the browser.

## Quick start

```bash
cd complyai/frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Use a projector-friendly fullscreen browser window.

## Judge flow (under 2 minutes)

1. Review the **compliance dashboard** and **status bar** (sample metrics).
2. **Download Latest Updates (PDF)** — official-style government bulletin (March 2026).
3. **Upload** a work permit (PDF / DOCX / TXT) or click **Use sample work permit** (John Smith sample is pre-loaded).
4. **Update My Work Permit** — 3-second “Applying 3 new regulations…” animation, then success.
5. Read **Change summary**, then **Download Updated Work Permit** (PDF).

## Stack

- React 18 + TypeScript + Vite
- Tailwind CSS
- `react-dropzone` — drag-and-drop upload
- `jspdf` — government update PDF + updated permit PDF
- `pdfjs-dist` — extract text from uploaded PDFs
- `mammoth` — extract text from DOCX

## Build

```bash
npm run build
npm run preview
```

## Notes

- Metrics (scores, pending counts) update after a successful **Update My Work Permit** action.
- If a PDF has no extractable text, use **TXT** or the **sample work permit**.
