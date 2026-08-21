import pytest
from worker.schemas.glossary import GlossaryData, GlossaryTerm
from worker.pipeline.translation import protect_glossary_terms, restore_glossary_terms, translate_manual
from worker.providers.translation.mock_provider import MockTranslationProvider
from worker.schemas.manual import ManualMaster, ManualMeta, ManualStep, StepEvidence, StepMedia

def test_glossary_protection_and_full_metadata_preservation():
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

    restored_vi = restore_glossary_terms("Nhấn {{TERM_002}} của thiết bị {{TERM_001}}.", p_map, "vi")
    assert "ABC-200" in restored_vi
    assert "nút START" in restored_vi

    # Test full metadata preservation during translation (P0-6)
    master = ManualMaster(
        manual=ManualMeta(
            title="操作マニュアル",
            source_language="ja",
            steps=[
                ManualStep(
                    step_id="step_001",
                    order=1,
                    title="起動",
                    instruction="STARTボタンを押す",
                    warning=None,
                    equipment=["STARTボタン"],
                    media=StepMedia(primary_frame_id="frame_001", additional_frame_ids=["frame_002"]),
                    evidence=StepEvidence(video_start=0.0, video_end=4.0, transcript_ids=["seg_001"], frame_ids=["frame_001"]),
                    evidence_score=0.85,
                    status="generated"
                )
            ]
        )
    )

    trans_provider = MockTranslationProvider()
    translated = translate_manual(master, ["vi", "id"], trans_provider, glossary)

    assert "vi" in translated
    vi_manual = translated["vi"]
    assert len(vi_manual.steps) == 1
    v_step = vi_manual.steps[0]
    
    # Verify all evidence/media/status are fully preserved
    assert v_step.step_id == "step_001"
    assert v_step.order == 1
    assert v_step.equipment == ["STARTボタン"]
    assert v_step.media.primary_frame_id == "frame_001"
    assert v_step.media.additional_frame_ids == ["frame_002"]
    assert v_step.evidence.video_start == 0.0
    assert v_step.evidence.video_end == 4.0
    assert v_step.evidence.transcript_ids == ["seg_001"]
    assert v_step.evidence.frame_ids == ["frame_001"]
    assert v_step.evidence_score == 0.85
    assert v_step.status == "generated"
