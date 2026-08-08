import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { LogOut, User, FileText, Database } from 'lucide-react';

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* الشعار والقوائم */}
          <div className="flex items-center space-x-8 space-x-reverse">
            <Link to="/" className="flex items-center space-x-2 space-x-reverse">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-xl font-bold text-gray-900">Ataeru</span>
            </Link>
            
            {isAuthenticated && (
              <div className="hidden md:flex items-center space-x-6 space-x-reverse">
                <Link
                  to="/dashboard"
                  className="text-gray-600 hover:text-primary-600 px-3 py-2 text-sm font-medium transition-colors"
                >
                  لوحة التحكم
                </Link>
                <Link
                  to="/knowledge"
                  className="text-gray-600 hover:text-primary-600 px-3 py-2 text-sm font-medium transition-colors flex items-center gap-1"
                >
                  <Database className="w-4 h-4" />
                  قاعدة المعرفة
                </Link>
                <Link
                  to="/rfp/new"
                  className="text-gray-600 hover:text-primary-600 px-3 py-2 text-sm font-medium transition-colors flex items-center gap-1"
                >
                  <FileText className="w-4 h-4" />
                  عطاء جديد
                </Link>
              </div>
            )}
          </div>

          {/* جانب المستخدم */}
          <div className="flex items-center space-x-4 space-x-reverse">
            {isAuthenticated ? (
              <>
                <div className="flex items-center space-x-3 space-x-reverse">
                  <div className="w-8 h-8 bg-accent-100 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-accent-700" />
                  </div>
                  <div className="hidden sm:block text-right">
                    <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                    <p className="text-xs text-gray-500">{user?.company?.name}</p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-gray-400 hover:text-red-500 transition-colors p-1.5"
                  title="تسجيل الخروج"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </>
            ) : (
              <div className="flex items-center space-x-2 space-x-reverse">
                <Link to="/login" className="btn-secondary text-sm">
                  تسجيل الدخول
                </Link>
                <Link to="/register" className="btn-primary text-sm">
                  ابدأ الآن
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}