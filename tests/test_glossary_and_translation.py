import pytest
from worker.schemas.glossary import GlossaryData, GlossaryTerm
from worker.pipeline.translation import protect_glossary_terms, restore_glossary_terms, translate_manual
from worker.providers.translation.mock_provider import MockTranslationProvider
from worker.schemas.manual import ManualMaster, ManualMeta, ManualStep, StepEvidence, StepMedia

def test_glossary_protection_and_restoration():
    glossary = GlossaryData(terms=[
        GlossaryTerm(source="ABC-200", translation={"vi": "ABC-200", "id": "ABC-200"}, translate=False),
        GlossaryTerm(source="STARTボタン", translation={"vi": "nút START", "id": "tombol START"}, translate=True)
    ])

    text = "装置 ABC-200 の STARTボタン を押してください。"
    protected, p_map = protect_glossary_terms(text, glossary)

    assert "ABC-200" not in protected
    assert "STARTボタン" not in protected
    assert "{{TERM_001}}" in protected
    assert "{{TERM_002}}" in protected

    # Test restoration for VI
    mock_translated_vi = "Nhấn {{TERM_002}} của thiết bị {{TERM_001}}."
    restored_vi = restore_glossary_terms(mock_translated_vi, p_map, "vi")
    assert "ABC-200" in restored_vi
    assert "nút START" in restored_vi
    assert "{{TERM_" not in restored_vi

    # Test restoration for ID
    mock_translated_id = "Tekan {{TERM_002}} dari perangkat {{TERM_001}}."
    restored_id = restore_glossary_terms(mock_translated_id, p_map, "id")
    assert "ABC-200" in restored_id
    assert "tombol START" in restored_id
