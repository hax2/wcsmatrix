# Repository conventions

- Keep API keys outside Git. Load an explicitly supplied env file; never log secrets or request headers.
- Preserve human, local, and frontier provenance. Frontier text is a source row, never relabeled human.
- Changes to inference settings require a new experiment name; changes to generation settings require new text paths.
- Keep the frozen prompts and pinned model/dataset revisions stable for the baseline.
- WCS is word-level all-subtoken survival. Report mean per-prompt scores and prompt-paired intervals.
- Never silently truncate source texts, impute missing matrix cells, or treat the draft's proposed E1–E4 as results.
- Use one GPU model at a time and respect hardware.vram_limit_gib. Server scoring is not validated until a real GPU smoke run passes.
- Check changes with `uv run ruff check src tests`, `uv run pytest -q`, and, where torch is installed, the optional chunked inference tests.
