---
name: file-converter
description: >
  Use when converting a file already on disk (PDF, image, document) into
  AI-friendly markdown, RAG chunks, a Karpathy-style wiki folder, or a
  knowledge-graph JSON. Trigger phrases: "convert this PDF to markdown",
  "extract the text from this document", "chunk this for RAG", "rip the
  tables out of this PDF", "preserve the multi-column layout", "build a
  knowledge graph from these docs", "I have a scanned document — get the
  text", "turn this file into markdown", "extract images from this PDF",
  "prep this doc for embedding". Runs via the `cnv` CLI (convert2) with
  XY-Cut++ layout recovery. Do NOT use for fetching a remote web page
  (use web-scraper or browser-control), for YouTube transcripts/audio
  (use youtube), or for packing a whole repo into a single file (use
  repomix).
---

# file-converter

<capabilities>
- Extracting text, tables, and images from PDFs.
- Preserving multi-column layouts and reading order using the XY-Cut++ algorithm.
- Converting documents to raw markdown, chunked RAG format, Karpathy-style wiki folders, or Knowledge Graph JSON.
</capabilities>

<instructions>
1. **Analyze the Request**: Determine the input files, the desired output format (`raw`, `rag`, `karpathy`, or `kg`), and the output destination.
2. **Verify Tooling**: Ensure the `cnv` CLI is available. If not, it can be installed via `cargo install --path ~/projects/convert2`.
3. **Execute Conversion**:
   - Run `cnv <INPUT> [OPTIONS]` to perform the conversion.
   - Use `-f <format>` to specify the format (e.g., `-f rag`).
   - Use `-o <output_dir>` to define the output directory.
   - If image extraction is not needed, use `--no-images` to speed up processing.
4. **Validate Output**: Confirm that the generated files exist and contain the expected structural content.
</instructions>
