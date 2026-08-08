import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { FileText, Database, CheckCircle, TrendingUp, PlusCircle, Loader2, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '@/services/api';
import { RFPAnalysisItem } from '@/types';

const STATUS_LABELS: Record<string, string> = {
  queued: 'في الانتظار',
  processing: 'جارٍ التحليل',
  completed: 'مكتمل',
  partially_completed: 'مكتمل جزئياً',
  failed: 'فشل',
  needs_review: 'يحتاج مراجعة',
};

const STATUS_COLORS: Record<string, string> = {
  queued: 'bg-gray-100 text-gray-700',
  processing: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  partially_completed: 'bg-amber-100 text-amber-700',
  failed: 'bg-red-100 text-red-700',
  needs_review: 'bg-amber-100 text-amber-700',
};

export default function Dashboard() {
  const { user } = useAuth();
  const [analyses, setAnalyses] = useState<RFPAnalysisItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<{ total: number; analyses: RFPAnalysisItem[] }>('/rfp/list')
      .then((res) => setAnalyses(res.data.analyses))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const completedCount = analyses.filter((a) => a.status === 'completed').length;
  const processingCount = analyses.filter((a) => a.status === 'queued' || a.status === 'processing').length;
  const failedCount = analyses.filter((a) => a.status === 'failed').length;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      {/* ترحيب */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          مرحباً، {user?.full_name} 👋
        </h1>
        <p className="text-gray-500 mt-1">
          {user?.company?.name} - خطة {user?.company?.subscription_plan === 'FREE' ? 'مجانية' : user?.company?.subscription_plan}
        </p>
      </div>

      {/* إحصائيات سريعة */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
            <FileText className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">العطاءات المحللة</p>
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin text-gray-400 mt-1" />
            ) : (
              <p className="text-2xl font-bold text-gray-900">{analyses.length}</p>
            )}
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
            <CheckCircle className="w-6 h-6 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">مكتملة بنجاح</p>
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin text-gray-400 mt-1" />
            ) : (
              <p className="text-2xl font-bold text-gray-900">{completedCount}</p>
            )}
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">قيد المعالجة / فشل</p>
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin text-gray-400 mt-1" />
            ) : (
              <p className="text-2xl font-bold text-gray-900">
                {processingCount} <span className="text-sm text-gray-400">/ {failedCount}</span>
              </p>
            )}
          </div>
        </div>
      </div>

      {/* إجراءات سريعة */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">إجراءات سريعة</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link
            to="/rfp/new"
            className="card hover:shadow-md transition-shadow flex items-center gap-4 cursor-pointer"
          >
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <PlusCircle className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900">رفع عطاء جديد</p>
              <p className="text-sm text-gray-500">حلل عطاءً واحصل على رد احترافي</p>
            </div>
          </Link>
          <Link
            to="/knowledge"
            className="card hover:shadow-md transition-shadow flex items-center gap-4 cursor-pointer"
          >
            <div className="w-10 h-10 bg-accent-100 rounded-lg flex items-center justify-center">
              <Database className="w-5 h-5 text-accent-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900">إدارة قاعدة المعرفة</p>
              <p className="text-sm text-gray-500">ارفع ملفات شركتك ومشاريعك السابقة</p>
            </div>
          </Link>
        </div>
      </div>

      {/* آخر التحليلات */}
      {analyses.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">آخر التحليلات</h2>
            <Link to="/rfp/new" className="text-sm text-primary-600 hover:text-primary-700 inline-flex items-center gap-1">
              عرض الكل <ArrowLeft className="w-4 h-4" />
            </Link>
          </div>
          <div className="card overflow-hidden p-0">
            <ul className="divide-y divide-gray-100">
              {analyses.slice(0, 5).map((a) => (
                <li key={a.id} className="px-6 py-3 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className="w-5 h-5 text-gray-400 shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">{a.filename}</p>
                      <p className="text-xs text-gray-400">
                        {new Date(a.created_at).toLocaleDateString('ar', {
                          year: 'numeric', month: 'short', day: 'numeric',
                        })}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {a.confidence_score > 0 && (
                      <span className="text-xs text-gray-500">ثقة {a.confidence_score}%</span>
                    )}
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[a.status] || 'bg-gray-100 text-gray-700'}`}>
                      {STATUS_LABELS[a.status] || a.status}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* رسالة تحفيزية */}
      {user?.company?.subscription_plan === 'FREE' && (
        <div className="card bg-gradient-to-r from-primary-50 to-blue-50 border-primary-100 mt-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-8 h-8 text-primary-600" />
              <div>
                <p className="font-semibold text-gray-900">أنت على الخطة المجانية</p>
                <p className="text-sm text-gray-600">حلل عطاءً واحداً مجاناً. قم بالترقية للوصول غير المحدود.</p>
              </div>
            </div>
            <Link to="/billing" className="btn-primary text-sm whitespace-nowrap">
              ترقية الخطة
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
