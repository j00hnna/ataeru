import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/hooks/useAuth';
import { Toaster } from 'react-hot-toast';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import Dashboard from '@/pages/Dashboard';
import KnowledgeBase from '@/pages/KnowledgeBase';
import NewRFP from '@/pages/NewRFP';
import ResponseViewer from '@/pages/ResponseViewer';
import Billing from '@/pages/Billing';
import Analytics from '@/pages/Analytics';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div></div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppLayout({ children }: { children: React.ReactNode }) {
  return <div className="min-h-screen flex flex-col"><Navbar /><main className="flex-1">{children}</main><Footer /></div>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/dashboard" element={<ProtectedRoute><AppLayout><Dashboard /></AppLayout></ProtectedRoute>} />
      <Route path="/knowledge" element={<ProtectedRoute><AppLayout><KnowledgeBase /></AppLayout></ProtectedRoute>} />
      <Route path="/rfp/new" element={<ProtectedRoute><AppLayout><NewRFP /></AppLayout></ProtectedRoute>} />
      <Route path="/rfp/:analysisId/response" element={<ProtectedRoute><AppLayout><ResponseViewer /></AppLayout></ProtectedRoute>} />
      <Route path="/billing" element={<ProtectedRoute><AppLayout><Billing /></AppLayout></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><AppLayout><Analytics /></AppLayout></ProtectedRoute>} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="top-center" toastOptions={{ duration: 4000, style: { fontFamily: 'Tajawal, sans-serif' } }} />
      </AuthProvider>
    </Router>
  );
}