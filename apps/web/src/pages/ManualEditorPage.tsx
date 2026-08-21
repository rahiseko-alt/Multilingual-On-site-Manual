import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import { Save, Languages, Download, AlertTriangle, Play, Check } from 'lucide-react';

export const ManualEditorPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [manual, setManual] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.getManual(id)
      .then((m) => setManual(m.data))
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [id]);

  const handleStepChange = (index: number, field: string, value: any) => {
    const updated = { ...manual };
    updated.manual.steps[index][field] = value;
    setManual(updated);
  };

  const handleSave = async () => {
    if (!id || !manual) return;
    setIsSaving(true);
    try {
      await api.updateManual(id, manual);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (e: any) {
      alert(e.message || '保存に失敗しました');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <div style={{ textAlign: 'center', padding: '48px' }}>マニュアルを読み込み中...</div>;
  }

  if (!manual) {
    return <div style={{ textAlign: 'center', padding: '48px' }}>マニュアルが見つかりません。動画の解析を行ってください。</div>;
  }

  const steps = manual.manual?.steps || [];

  return (
    <div>
      {/* Action Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h1 style={{ margin: '0 0 4px', fontSize: '22px', color: '#0f172a' }}>{manual.manual?.title}</h1>
          <div style={{ fontSize: '13px', color: '#64748b' }}>
            原言語: {manual.manual?.source_language} | ステップ数: {steps.length}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Link
            to={`/projects/${id}/translations`}
            style={{ background: '#f8fafc', border: '1px solid #cbd5e1', color: '#334155', textDecoration: 'none', padding: '8px 14px', borderRadius: '6px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Languages size={16} /> 多言語翻訳の確認
          </Link>
          <Link
            to={`/projects/${id}/export`}
            style={{ background: '#f8fafc', border: '1px solid #cbd5e1', color: '#334155', textDecoration: 'none', padding: '8px 14px', borderRadius: '6px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Download size={16} /> 出力・ダウンロード
          </Link>
          <button
            onClick={handleSave}
            disabled={isSaving}
            style={{ background: '#2563eb', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 'bold', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}
          >
            {saveSuccess ? <Check size={16} /> : <Save size={16} />}
            {isSaving ? '保存中...' : saveSuccess ? '保存完了' : 'マニュアルを保存'}
          </button>
        </div>
      </div>

      {/* Steps List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {steps.map((st: any, idx: number) => {
          const isNeedsReview = st.status === 'needs_review';

          return (
            <div
              key={st.step_id || idx}
              style={{
                background: '#ffffff',
                border: isNeedsReview ? '2px dashed #f59e0b' : '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '20px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ background: '#2563eb', color: 'white', fontWeight: 'bold', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' }}>
                    Step {st.order}
                  </span>
                  <input
                    type="text"
                    value={st.title}
                    onChange={(e) => handleStepChange(idx, 'title', e.target.value)}
                    style={{ fontSize: '15px', fontWeight: 'bold', border: '1px solid #cbd5e1', borderRadius: '4px', padding: '4px 8px', width: '320px' }}
                  />
                </div>
                {isNeedsReview && (
                  <span style={{ background: '#fef3c7', color: '#92400e', padding: '3px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px', border: '1px solid #f59e0b' }}>
                    <AlertTriangle size={14} /> 要確認 (根拠スコア: {st.evidence_score?.toFixed(2)})
                  </span>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: '20px' }}>
                {/* Step Image */}
                <div style={{ background: '#f1f5f9', borderRadius: '6px', height: '120px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: '12px' }}>
                  {st.media?.primary_frame_id ? `画像: ${st.media.primary_frame_id}` : 'No Image'}
                </div>

                {/* Step Content */}
                <div>
                  <div style={{ marginBottom: '12px' }}>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '4px', color: '#475569' }}>作業手順 (Instruction)</label>
                    <textarea
                      rows={3}
                      value={st.instruction}
                      onChange={(e) => handleStepChange(idx, 'instruction', e.target.value)}
                      style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                    />
                  </div>

                  {st.warning && (
                    <div style={{ marginBottom: '12px', background: '#fffbeb', borderLeft: '3px solid #f59e0b', padding: '6px 10px', borderRadius: '2px', fontSize: '12px', color: '#92400e' }}>
                      ⚠️ 注意事項: {st.warning}
                    </div>
                  )}

                  {/* Evidence Footer */}
                  <div style={{ fontSize: '12px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '16px', borderTop: '1px dashed #e2e8f0', paddingTop: '8px', marginTop: '8px' }}>
                    <span>🎬 該当時間: {st.evidence?.video_start?.toFixed(1)}s - {st.evidence?.video_end?.toFixed(1)}s</span>
                    <span>充足スコア: {st.evidence_score?.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
