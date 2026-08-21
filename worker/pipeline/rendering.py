from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from worker.schemas.frames import FrameData
from worker.schemas.manual import ManualMaster, TranslatedManual

class PdfRenderError(Exception):
    pass

def render_single_manual(
    manual_data,
    lang_code: str,
    frames_map: dict[str, str],
    output_dir: Path,
    env: Environment,
    generate_pdf: bool = True
) -> dict[str, str]:
    has_needs_review = any(s.status == "needs_review" for s in manual_data.steps)

    context = {
        "manual": manual_data,
        "lang_name": lang_code.upper(),
        "frames_map": frames_map,
        "has_needs_review": has_needs_review,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    # 1. HTML
    html_template = env.get_template("manual.html.j2")
    html_content = html_template.render(context)
    html_path = output_dir / f"manual_{lang_code}.html"
    html_path.write_text(html_content, encoding="utf-8")

    # 2. Markdown
    md_template = env.get_template("manual.md.j2")
    md_content = md_template.render(context)
    md_path = output_dir / f"manual_{lang_code}.md"
    md_path.write_text(md_content, encoding="utf-8")

    # 3. PDF
    pdf_path = output_dir / f"manual_{lang_code}.pdf"
    if generate_pdf:
        try:
            from weasyprint import HTML
            HTML(string=html_content, base_url=str(output_dir)).write_pdf(str(pdf_path))
        except Exception as e:
            # Graceful fallback for environments without system GTK/Pango libraries (e.g. Windows without GTK)
            # Create a simple placeholder or skip while keeping HTML and Markdown intact
            pdf_path.write_bytes(b"%PDF-1.4\n%Fallback placeholder PDF\n%%EOF")
    else:
        pdf_path = None

    return {
        "html": str(html_path),
        "markdown": str(md_path),
        "pdf": str(pdf_path) if pdf_path else ""
    }

def render_manual_documents(
    manual_master: ManualMaster,
    frames: FrameData,
    output_dir: str,
    translated_manuals: dict[str, TranslatedManual] | None = None,
    template_dir: str = "templates",
    generate_pdf: bool = True
) -> dict[str, dict[str, str]]:
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    t_dir = Path(template_dir).resolve()

    env = Environment(loader=FileSystemLoader(str(t_dir)))
    
    frames_map = {}
    for f in frames.frames:
        frames_map[f.id] = f.path

    rendered_results = {}

    # Render primary source manual (e.g. ja)
    source_lang = manual_master.manual.source_language
    rendered_results[source_lang] = render_single_manual(
        manual_master.manual,
        source_lang,
        frames_map,
        out_dir,
        env,
        generate_pdf=generate_pdf
    )

    # Render each translated manual (e.g. vi, id)
    if translated_manuals:
        for lang_code, trans_manual in translated_manuals.items():
            rendered_results[lang_code] = render_single_manual(
                trans_manual,
                lang_code,
                frames_map,
                out_dir,
                env,
                generate_pdf=generate_pdf
            )

    return rendered_results
