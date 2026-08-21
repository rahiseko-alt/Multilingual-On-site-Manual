# CLAUDE.md

## Video2Doc MultiLang Core Rules

This project is an evidence-first video-to-manual system.

Never generate operational facts that are not supported by transcript or visual evidence.

The canonical artifact is `manual_master.json`.

PDF, HTML and Markdown are derived artifacts.

Do not couple API routes directly to AI models.

All AI models must be accessed through provider interfaces (`TranscriptionProvider`, `VisionProvider`, `TranslationProvider`, `StorageProvider`).

The development environment must support CPU-only execution.

Reuse mature OSS before implementing equivalent functionality.

Implement one phase at a time (CLI Engine -> API -> Worker -> DB/Storage -> PWA -> SaaS).

Do not implement future features unless explicitly requested.

Every generated manual step must preserve references to its source video evidence (`video_start`, `video_end`, `transcript_ids`, `frame_ids`).

Do not mark a phase complete only because tests pass. Run the actual pipeline against fixture media and inspect the generated artifacts.

---

## Development Workflow
- Follow the 4-tier rule hierarchy in `AGENTS.md`.
- Session in: Read `docs/handoff.md`, check git status.
- Session out: Update `docs/handoff.md`, append to `docs/failures.md` if any failure occurred.
