# file-converter

<description>
File format conversion and extraction expert. Use when you need to convert PDF documents, images, or other complex file types into AI-friendly markdown or structured formats using `cnv` (convert2). Covers text extraction, layout recovery, chunking for RAG, and knowledge graph generation from documents.
</description>

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
