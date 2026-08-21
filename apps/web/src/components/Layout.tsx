import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FileText, Folder, LogOut, Video } from 'lucide-react';

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ background: '#1e3a8a', color: 'white', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Link to="/projects" style={{ color: 'white', textDecoration: 'none', fontSize: '18px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Video size={24} /> Video2Doc MultiLang
          </Link>
          <nav style={{ display: 'flex', gap: '12px', marginLeft: '24px' }}>
            <Link to="/projects" style={{ color: '#bfdbfe', textDecoration: 'none', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Folder size={16} /> プロジェクト
            </Link>
          </nav>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {user && (
            <span style={{ fontSize: '13px', color: '#93c5fd' }}>
              {user.full_name || user.email}
            </span>
          )}
          <button
            onClick={handleLogout}
            style={{ background: 'transparent', border: '1px solid #60a5fa', color: '#ffffff', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}
          >
            <LogOut size={14} /> ログアウト
          </button>
        </div>
      </header>
      <main style={{ flex: 1, padding: '24px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
        <Outlet />
      </main>
      <footer style={{ background: '#ffffff', borderTop: '1px solid #e2e8f0', padding: '16px', textAlign: 'center', fontSize: '12px', color: '#64748b' }}>
        Video2Doc MultiLang v1.0 &copy; 2026 - PWA On-site Manual Generator
      </footer>
    </div>
  );
};
