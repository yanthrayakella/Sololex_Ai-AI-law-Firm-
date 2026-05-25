import { jsPDF } from "jspdf";

/** Multipage PDF from plain text for updated work permit download */
export function downloadUpdatedWorkPermitPdf(fullText: string, filename: string) {
  const doc = new jsPDF({ unit: "pt", format: "letter" });
  const margin = 48;
  const maxWidth = 515;
  let y = margin;
  const pageHeight = doc.internal.pageSize.getHeight();
  const lineHeight = 12;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);

  const paragraphs = fullText.split(/\n\n+/);
  for (const para of paragraphs) {
    const lines = doc.splitTextToSize(para.replace(/\n/g, " "), maxWidth);
    for (const line of lines) {
      if (y > pageHeight - margin) {
        doc.addPage();
        y = margin;
      }
      doc.text(line, margin, y);
      y += lineHeight;
    }
    y += lineHeight * 0.5;
  }

  doc.save(filename);
}

export function downloadUpdatedWorkPermitTxt(fullText: string) {
  const blob = new Blob([fullText], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "updated-work-permit-march-2026.txt";
  a.click();
  URL.revokeObjectURL(url);
}
