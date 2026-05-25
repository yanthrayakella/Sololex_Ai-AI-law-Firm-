import { SAMPLE_WORK_PERMIT } from "../data/sampleWorkPermit";

/** Appends March 2026 regulatory compliance block per judge demo spec */
export function mergeWorkPermitWithRegulations(
  originalText: string,
  complianceDate: string
): string {
  const trimmed = originalText.trim() || SAMPLE_WORK_PERMIT.trim();
  const divider = "\n" + "=".repeat(72) + "\n";

  const summaryHeader = "UPDATED TO COMPLY WITH MARCH 2026 REGULATIONS\n";

  const sections = `
SECTION: Digital Identity Verification Code
Requirement: Must obtain and include verification code from Ministry.
Status: Pending — Code required before submission.

SECTION: Health Insurance Requirement
Requirement: Proof of private health insurance for full employment period.
Status: Documentation required.

SECTION: Employer Sponsorship Documentation
Requirement: Additional hiring justification documents required.
Status: Submit job posting records and interview summaries.
`.trim();

  const footer = `
This document was auto-updated by ComplyAI on ${complianceDate} to reflect
Work Permit Amendment 2026-03. All changes are highlighted for your review.
`.trim();

  return `${trimmed}${divider}${summaryHeader}\n${sections}\n${divider}${footer}\n`;
}

export const CHANGE_SUMMARY_ITEMS = [
  "Added Digital Identity Verification Code requirement",
  "Added Health Insurance Proof requirement",
  "Added Employer Sponsorship Documentation requirement",
] as const;
