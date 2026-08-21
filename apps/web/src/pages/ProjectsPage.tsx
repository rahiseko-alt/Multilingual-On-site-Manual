import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { Plus, Video, Clock, CheckCircle2, ChevronRight, FileText } from 'lucide-react';

export const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [sourceLang, setSourceLang] = useState('ja');
  const [targetLangs, setTargetLangs] = useState('vi,id');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const navigate = useNavigate();

  const loadProjects = async () => {
    try {
      const list = await api.getProjects();
      setProjects(list);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle) return;
    setIsCreating(true);
    try {
      const proj = await api.createProject({
        title: newTitle,
        source_language: sourceLang,
        target_languages: targetLangs,
      });

      if (selectedFile) {
        await api.uploadVideo(proj.id, selectedFile);
        const job = await api.startProcessing(proj.id);
        navigate(`/projects/${proj.id}/processing?job=${job.job_id}`);
      } else {
        navigate(`/projects/${proj.id}/manual`);
      }
    } catch (err: any) {
      alert(err.message || '作成に失敗しました');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ margin: '0 0 4px', fontSize: '24px', color: '#0f172a' }}>マニュアルプロジェクト</h1>
          <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>動画から生成されたマニュアルを管理・編集します</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          style={{ background: '#2563eb', color: 'white', border: 'none', borderRadius: '6px', padding: '10px 16px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
        >
          <Plus size={18} /> 新規マニュアル作成
        </button>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#94a3b8' }}>読み込み中...</div>
      ) : projects.length === 0 ? (
        <div style={{ background: '#ffffff', border: '1px dashed #cbd5e1', borderRadius: '12px', padding: '48px', textAlign: 'center' }}>
          <Video size={48} style={{ color: '#94a3b8', marginBottom: '16px' }} />
          <h3 style={{ margin: '0 0 8px', color: '#334155' }}>プロジェクトがありません</h3>
          <p style={{ margin: '0 0 16px', color: '#64748b', fontSize: '14px' }}>現場作業動画をアップロードして、多言語マニュアルを自動生成しましょう。</p>
          <button
            onClick={() => setIsModalOpen(true)}
            style={{ background: '#2563eb', color: 'white', border: 'none', borderRadius: '6px', padding: '8px 16px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            最初のマニュアルを作成
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
          {projects.map((p) => (
            <div
              key={p.id}
              onClick={() => navigate(`/projects/${p.id}/manual`)}
              style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', cursor: 'pointer', transition: 'box-shadow 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <h3 style={{ margin: 0, fontSize: '16px', color: '#1e3a8a' }}>{p.title}</h3>
                <ChevronRight size={18} style={{ color: '#94a3b8' }} />
              </div>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '8px' }}>
                言語: {p.source_language} &rarr; {p.target_languages}
              </div>
              <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={14} /> {new Date(p.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}

      {isModalOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
          <div style={{ background: '#ffffff', borderRadius: '12px', padding: '28px', maxWidth: '480px', width: '100%' }}>
            <h2 style={{ margin: '0 0 16px', fontSize: '18px' }}>新規マニュアル作成</h2>
            <form onSubmit={handleCreate}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '6px' }}>マニュアルタイトル</label>
                <input
                  type="text"
                  required
                  placeholder="例: NC旋盤 起動・材料投入手順"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '6px' }}>作業動画 (MP4)</label>
                <input
                  type="file"
                  accept="video/mp4,video/*"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  style={{ width: '100%', fontSize: '13px' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '6px' }}>動画の言語</label>
                  <select
                    value={sourceLang}
                    onChange={(e) => setSourceLang(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                  >
                    <option value="ja">日本語 (Japanese)</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '6px' }}>翻訳先言語</label>
                  <input
                    type="text"
                    value={targetLangs}
                    onChange={(e) => setTargetLangs(e.target.value)}
                    placeholder="vi,id"
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  style={{ background: '#f1f5f9', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}
                >
                  キャンセル
                </button>
                <button
                  type="submit"
                  disabled={isCreating}
                  style={{ background: '#2563eb', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}
                >
                  {isCreating ? '作成・アップロード中...' : 'マニュアルを作成'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
