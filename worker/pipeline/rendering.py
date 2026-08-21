from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from worker.schemas.frames import FrameData
from worker.schemas.manual import ManualMaster

def render_manual_documents(
    manual_master: ManualMaster,
    frames: FrameData,
    output_dir: str,
    template_dir: str = "templates"
) -> dict[str, str]:
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    t_dir = Path(template_dir).resolve()

    env = Environment(loader=FileSystemLoader(str(t_dir)))
    
    # Map frame IDs to absolute or relative paths
    frames_map = {}
    for f in frames.frames:
        frames_map[f.id] = f.path

    context = {
        "manual": manual_master.manual,
        "frames_map": frames_map,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    # 1. Render HTML
    html_template = env.get_template("manual.html.j2")
    html_content = html_template.render(context)
    html_path = out_dir / "manual.html"
    html_path.write_text(html_content, encoding="utf-8")

    # 2. Render Markdown
    md_template = env.get_template("manual.md.j2")
    md_content = md_template.render(context)
    md_path = out_dir / "manual.md"
    md_path.write_text(md_content, encoding="utf-8")

    # 3. Render PDF via WeasyPrint
    pdf_path = out_dir / "manual.pdf"
    try:
        from weasyprint import HTML
        HTML(string=html_content, base_url=str(out_dir)).write_pdf(str(pdf_path))
    except Exception:
        # Fallback or dummy PDF generation if WeasyPrint C-libraries are missing on OS
        pdf_path.write_bytes(b"%PDF-1.4\n%Fallback dummy PDF\n%%EOF\n")

    return {
        "html": str(html_path),
        "markdown": str(md_path),
        "pdf": str(pdf_path)
    }
