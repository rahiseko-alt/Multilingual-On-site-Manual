import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import { ArrowLeft, Save, Check } from 'lucide-react';

export const TranslationsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [selectedLang, setSelectedLang] = useState('vi');
  const [translation, setTranslation] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (!id) return;
    setIsLoading(true);
    api.getTranslation(id, selectedLang)
      .then((t) => setTranslation(t))
      .catch(() => setTranslation(null))
      .finally(() => setIsLoading(false));
  }, [id, selectedLang]);

  const handleStepChange = (index: number, field: string, value: any) => {
    const updated = { ...translation };
    updated.steps[index][field] = value;
    setTranslation(updated);
  };

  const handleSave = async () => {
    if (!id || !translation) return;
    setIsSaving(true);
    try {
      await api.updateTranslation(id, selectedLang, translation);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (e: any) {
      alert(e.message || '保存に失敗しました');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Link to={`/projects/${id}/manual`} style={{ color: '#64748b', display: 'flex', alignItems: 'center' }}>
            <ArrowLeft size={20} />
          </Link>
          <h1 style={{ margin: 0, fontSize: '20px', color: '#0f172a' }}>多言語翻訳の確認・編集</h1>
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving || !translation}
          style={{ background: '#2563eb', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 'bold', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}
        >
          {saveSuccess ? <Check size={16} /> : <Save size={16} />}
          {isSaving ? '保存中...' : saveSuccess ? '保存完了' : '翻訳を保存'}
        </button>
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button
          onClick={() => setSelectedLang('vi')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: selectedLang === 'vi' ? '2px solid #2563eb' : '1px solid #cbd5e1', background: selectedLang === 'vi' ? '#eff6ff' : '#ffffff', fontWeight: selectedLang === 'vi' ? 'bold' : 'normal', cursor: 'pointer' }}
        >
          🇻🇳 ベトナム語 (Tiếng Việt)
        </button>
        <button
          onClick={() => setSelectedLang('id')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: selectedLang === 'id' ? '2px solid #2563eb' : '1px solid #cbd5e1', background: selectedLang === 'id' ? '#eff6ff' : '#ffffff', fontWeight: selectedLang === 'id' ? 'bold' : 'normal', cursor: 'pointer' }}
        >
          🇮🇩 インドネシア語 (Bahasa Indonesia)
        </button>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '48px' }}>翻訳データを読み込み中...</div>
      ) : !translation ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#94a3b8' }}>この言語の翻訳データがありません</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ background: '#ffffff', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '4px' }}>翻訳タイトル</label>
            <input
              type="text"
              value={translation.title}
              onChange={(e) => setTranslation({ ...translation, title: e.target.value })}
              style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
            />
          </div>

          {translation.steps?.map((st: any, idx: number) => (
            <div key={st.step_id || idx} style={{ background: '#ffffff', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                <span style={{ background: '#64748b', color: 'white', fontSize: '12px', padding: '2px 6px', borderRadius: '4px' }}>Step {st.order}</span>
                <input
                  type="text"
                  value={st.title}
                  onChange={(e) => handleStepChange(idx, 'title', e.target.value)}
                  style={{ width: '300px', padding: '4px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '14px', fontWeight: 'bold' }}
                />
              </div>
              <div>
                <textarea
                  rows={2}
                  value={st.instruction}
                  onChange={(e) => handleStepChange(idx, 'instruction', e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
