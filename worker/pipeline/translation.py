import re
from pathlib import Path
from worker.providers.translation.base import TranslationProvider
from worker.schemas.glossary import GlossaryData
from worker.schemas.manual import ManualMaster, TranslatedManual, TranslatedStep

def protect_glossary_terms(text: str, glossary: GlossaryData) -> tuple[str, dict[str, str]]:
    if not text or not glossary or not glossary.terms:
        return text, {}

    protected_text = text
    placeholder_map = {}

    for i, term in enumerate(glossary.terms, start=1):
        if not term.source:
            continue
        placeholder = f"{{{{TERM_{i:03d}}}}}"
        # If term is in text, replace
        if term.source in protected_text:
            placeholder_map[placeholder] = term
            protected_text = protected_text.replace(term.source, placeholder)

    return protected_text, placeholder_map

def restore_glossary_terms(translated_text: str, placeholder_map: dict[str, any], target_lang: str) -> str:
    if not translated_text or not placeholder_map:
        return translated_text

    result = translated_text
    for placeholder, term in placeholder_map.items():
        if placeholder in result:
            if not term.translate:
                # Keep original source
                replacement = term.source
            else:
                replacement = term.translation.get(target_lang, term.source)
            result = result.replace(placeholder, replacement)

    return result

def translate_manual(
    manual_master: ManualMaster,
    target_languages: list[str],
    provider: TranslationProvider,
    glossary: GlossaryData | None = None,
    output_dir: str | None = None
) -> dict[str, TranslatedManual]:
    source_lang = manual_master.manual.source_language
    results = {}

    for t_lang in target_languages:
        # Translate title
        p_title, p_map_title = protect_glossary_terms(manual_master.manual.title, glossary)
        trans_title_raw = provider.translate(p_title, source_lang, t_lang)
        final_title = restore_glossary_terms(trans_title_raw, p_map_title, t_lang)

        translated_steps = []
        for step in manual_master.manual.steps:
            # Step title
            p_st, p_map_st = protect_glossary_terms(step.title, glossary)
            t_st_raw = provider.translate(p_st, source_lang, t_lang)
            final_st = restore_glossary_terms(t_st_raw, p_map_st, t_lang)

            # Step instruction
            p_inst, p_map_inst = protect_glossary_terms(step.instruction, glossary)
            t_inst_raw = provider.translate(p_inst, source_lang, t_lang)
            final_inst = restore_glossary_terms(t_inst_raw, p_map_inst, t_lang)

            # Warning if any
            final_warn = None
            if step.warning:
                p_warn, p_map_warn = protect_glossary_terms(step.warning, glossary)
                t_warn_raw = provider.translate(p_warn, source_lang, t_lang)
                final_warn = restore_glossary_terms(t_warn_raw, p_map_warn, t_lang)

            translated_steps.append(
                TranslatedStep(
                    step_id=step.step_id,
                    order=step.order,
                    title=final_st,
                    instruction=final_inst,
                    warning=final_warn
                )
            )

        trans_manual = TranslatedManual(
            title=final_title,
            source_language=source_lang,
            target_language=t_lang,
            steps=translated_steps
        )
        results[t_lang] = trans_manual

        if output_dir:
            out_file = Path(output_dir) / f"manual_{t_lang}.json"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(trans_manual.model_dump_json(indent=2), encoding="utf-8")

    return results
