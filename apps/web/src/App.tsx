import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { ManualEditorPage } from './pages/ManualEditorPage';
import { TranslationsPage } from './pages/TranslationsPage';
import { ExportPage } from './pages/ExportPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, isLoading } = useAuth();
  if (isLoading) return <div>読み込み中...</div>;
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/projects" replace />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="projects/:id/processing" element={<ProcessingPage />} />
            <Route path="projects/:id/manual" element={<ManualEditorPage />} />
            <Route path="projects/:id/translations" element={<TranslationsPage />} />
            <Route path="projects/:id/export" element={<ExportPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};
