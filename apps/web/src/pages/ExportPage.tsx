import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import { ArrowLeft, Download, FileCode, FileText, CheckCircle2 } from 'lucide-react';

export const ExportPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [selectedLang, setSelectedLang] = useState('ja');
  const [isExporting, setIsExporting] = useState(false);

  const handleDownload = async (format: string) => {
    if (!id) return;
    setIsExporting(true);
    try {
      const res = await api.createExport(id, format, selectedLang);
      window.open(res.download_url, '_blank');
    } catch (e: any) {
      alert(e.message || 'エクスポートに失敗しました');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <Link to={`/projects/${id}/manual`} style={{ color: '#64748b' }}>
          <ArrowLeft size={20} />
        </Link>
        <h1 style={{ margin: 0, fontSize: '22px', color: '#0f172a' }}>マニュアルの出力・ダウンロード</h1>
      </div>

      <div style={{ background: '#ffffff', borderRadius: '12px', padding: '24px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '8px' }}>出力言語の選択</label>
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
          >
            <option value="ja">🇯🇵 日本語 (Japanese)</option>
            <option value="vi">🇻🇳 ベトナム語 (Tiếng Việt)</option>
            <option value="id">🇮🇩 インドネシア語 (Bahasa Indonesia)</option>
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <button
            onClick={() => handleDownload('html')}
            disabled={isExporting}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#f8fafc', cursor: 'pointer', textAlign: 'left' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <FileCode size={24} style={{ color: '#2563eb' }} />
              <div>
                <strong style={{ display: 'block', fontSize: '14px' }}>HTML マニュアル</strong>
                <span style={{ fontSize: '12px', color: '#64748b' }}>ブラウザ閲覧・社内ポータル埋め込み用</span>
              </div>
            </div>
            <Download size={18} style={{ color: '#64748b' }} />
          </button>

          <button
            onClick={() => handleDownload('md')}
            disabled={isExporting}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#f8fafc', cursor: 'pointer', textAlign: 'left' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <FileText size={24} style={{ color: '#059669' }} />
              <div>
                <strong style={{ display: 'block', fontSize: '14px' }}>Markdown マニュアル</strong>
                <span style={{ fontSize: '12px', color: '#64748b' }}>Notion / GitHub / Wiki 連携用</span>
              </div>
            </div>
            <Download size={18} style={{ color: '#64748b' }} />
          </button>

          <button
            onClick={() => handleDownload('pdf')}
            disabled={isExporting}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#f8fafc', cursor: 'pointer', textAlign: 'left' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <FileText size={24} style={{ color: '#dc2626' }} />
              <div>
                <strong style={{ display: 'block', fontSize: '14px' }}>PDF ドキュメント</strong>
                <span style={{ fontSize: '12px', color: '#64748b' }}>現場印刷・配布用 A4 マニュアル</span>
              </div>
            </div>
            <Download size={18} style={{ color: '#64748b' }} />
          </button>
        </div>
      </div>
    </div>
  );
};
