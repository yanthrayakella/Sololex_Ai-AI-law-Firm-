import { jsPDF } from "jspdf";

const BLOCK: string[] = [
  "OFFICIAL GOVERNMENT UPDATE",
  "Ministry of Human Resources and Social Security",
  "",
  "Issue Date: March 28, 2026",
  "Effective: April 15, 2026",
  "",
  "UPDATE #1: Digital Identity Verification Code",
  "All work permit applications must now include a digital identity",
  "verification code in Section 7. This code will be issued by the",
  "Ministry upon application submission.",
  "",
  "UPDATE #2: Health Insurance Requirement",
  "Foreign workers must now provide proof of private health insurance",
  "coverage for the entire duration of their employment. Previously,",
  "this was only required for workers from non-reciprocal countries.",
  "",
  "UPDATE #3: Employer Sponsorship Documentation",
  "Employers must now submit additional documentation proving",
  "the position could not be filled by a local candidate. This",
  "includes 30 days of job posting records and interview summaries.",
  "",
  "Non-compliance Penalties:",
  "",
  "First offense: ¥50,000 - ¥100,000",
  "",
  "Repeated offense: ¥200,000 - ¥500,000",
  "",
  "Business license suspension for severe cases",
  "",
  "For questions, contact: workpermit@mohrss.gov.cn",
];

export function downloadGovernmentUpdatesPdf() {
  const doc = new jsPDF({ unit: "pt", format: "letter" });
  const margin = 56;
  let y = 48;
  const pageHeight = doc.internal.pageSize.getHeight();
  const baseLine = 13;

  for (let i = 0; i < BLOCK.length; i++) {
    const line = BLOCK[i];
    if (y > pageHeight - margin) {
      doc.addPage();
      y = margin;
    }
    if (line === "") {
      y += baseLine * 0.5;
      continue;
    }

    if (i === 0) {
      doc.setFont("helvetica", "bold");
      doc.setFontSize(15);
    } else if (i === 1) {
      doc.setFont("helvetica", "normal");
      doc.setFontSize(11);
    } else {
      doc.setFontSize(10);
    }

    const boldLine =
      line.startsWith("UPDATE #") ||
      line === "Non-compliance Penalties:" ||
      line.startsWith("First offense:") ||
      line.startsWith("Repeated offense:") ||
      line.startsWith("Business license suspension");

    doc.setFont("helvetica", boldLine ? "bold" : "normal");
    const wrapped = doc.splitTextToSize(line, 500);
    doc.text(wrapped, margin, y);
    y += baseLine * Math.max(1, wrapped.length);
  }

  doc.save("Government Updates — Work Permit Regulations (March 2026).pdf");
}
