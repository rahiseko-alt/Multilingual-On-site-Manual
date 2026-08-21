import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import { CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react';

export const ProcessingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('job');
  const navigate = useNavigate();

  const [job, setJob] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const stages = [
    { key: 'validation', label: '1. 音声を解析' },
    { key: 'scenes', label: '2. 作業場面を抽出' },
    { key: 'vision', label: '3. 作業内容を解析中…' },
    { key: 'manual', label: '4. マニュアルを作成' },
    { key: 'translation', label: '5. 翻訳' },
  ];

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const j = await api.getJob(jobId);
        setJob(j);

        if (j.status === 'completed') {
          clearInterval(interval);
          setTimeout(() => navigate(`/projects/${id}/manual`), 1200);
        } else if (j.status === 'failed') {
          clearInterval(interval);
          setError(j.error || '解析処理中にエラーが発生しました');
        }
      } catch (err: any) {
        console.error(err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId, id, navigate]);

  return (
    <div style={{ maxWidth: '600px', margin: '48px auto', background: '#ffffff', padding: '36px', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}>
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <h2 style={{ margin: '0 0 8px', fontSize: '20px', color: '#0f172a' }}>動画を解析しています</h2>
        <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>AI が作業動画から根拠（Evidence）を抽出しています</p>
      </div>

      {error ? (
        <div style={{ background: '#fef2f2', border: '1px solid #ef4444', color: '#b91c1c', padding: '16px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertCircle size={24} />
          <div>
            <strong>解析失敗:</strong> {error}
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {stages.map((st, idx) => {
            const isCompleted = job && (job.progress > (idx + 1) * 20 || job.status === 'completed');
            const isCurrent = job && !isCompleted && job.status !== 'failed';

            return (
              <div
                key={st.key}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  background: isCurrent ? '#eff6ff' : '#f8fafc',
                  border: isCurrent ? '1px solid #bfdbfe' : '1px solid #e2e8f0',
                }}
              >
                {isCompleted ? (
                  <CheckCircle2 size={20} style={{ color: '#16a34a' }} />
                ) : isCurrent ? (
                  <Loader2 size={20} style={{ color: '#2563eb', animation: 'spin 1s linear infinite' }} />
                ) : (
                  <Circle size={20} style={{ color: '#cbd5e1' }} />
                )}
                <span style={{ fontSize: '14px', fontWeight: isCurrent ? 'bold' : 'normal', color: isCompleted ? '#16a34a' : isCurrent ? '#1e3a8a' : '#64748b' }}>
                  {st.label}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
