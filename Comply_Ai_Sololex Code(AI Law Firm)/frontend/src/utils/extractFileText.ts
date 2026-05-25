import mammoth from "mammoth";
import * as pdfjs from "pdfjs-dist";

import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;

export async function extractTextFromFile(file: File): Promise<string> {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";

  if (ext === "txt") {
    return file.text();
  }

  if (ext === "docx") {
    const buf = await file.arrayBuffer();
    const result = await mammoth.extractRawText({ arrayBuffer: buf });
    return result.value || "";
  }

  if (ext === "pdf") {
    const buf = await file.arrayBuffer();
    const pdf = await pdfjs.getDocument({ data: new Uint8Array(buf) }).promise;
    const pages: string[] = [];
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      const strings = content.items.map((item) =>
        "str" in item ? item.str : ""
      );
      pages.push(strings.join(" "));
    }
    return pages.join("\n\n");
  }

  throw new Error("Unsupported file type. Use PDF, DOCX, or TXT.");
}
