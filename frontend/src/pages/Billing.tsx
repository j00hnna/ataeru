import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { CreditCard, CheckCircle } from 'lucide-react';
import api from '@/services/api';
import toast from 'react-hot-toast';

export default function Billing() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async (plan: string) => {
    setLoading(true);
    try {
      const res = await api.post(`/billing/create-checkout?plan=${plan}`);
      window.location.href = res.data.url;
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل إنشاء جلسة الدفع');
    } finally {
      setLoading(false);
    }
  };

  const currentPlan = user?.company?.subscription_plan;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">الاشتراكات والفوترة</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* خطة مجانية */}
        <div className={`card border-2 ${currentPlan === 'FREE' ? 'border-primary-500' : 'border-gray-200'}`}>
          <h2 className="text-lg font-semibold">مجانية</h2>
          <p className="text-3xl font-bold mt-2">0$</p>
          <ul className="mt-4 space-y-2 text-sm text-gray-600">
            <li className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-500" /> تحليل عطاء واحد</li>
            <li className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-500" /> معاينة النتائج</li>
          </ul>
          {currentPlan === 'FREE' && <p className="mt-4 text-primary-600 font-medium">خطتك الحالية</p>}
        </div>
        {/* خطة Pro */}
        <div className={`card border-2 ${currentPlan === 'PRO' ? 'border-primary-500' : 'border-gray-200'}`}>
          <h2 className="text-lg font-semibold">Pro</h2>
          <p className="text-3xl font-bold mt-2">500$<span className="text-sm text-gray-500">/شهر</span></p>
          <ul className="mt-4 space-y-2 text-sm text-gray-600">
            <li className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-500" /> عطاءات غير محدودة</li>
            <li className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-500" /> توليد ردود كاملة</li>
            <li className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-500" /> تدقيق الامتثال</li>
          </ul>
          {currentPlan === 'PRO' ? (
            <p className="mt-4 text-primary-600 font-medium">خطتك الحالية</p>
          ) : (
            <button onClick={() => handleUpgrade('PRO')} disabled={loading} className="btn-primary w-full mt-4">
              <CreditCard className="w-4 h-4 ml-1" /> ترقية
            </button>
          )}
        </div>
        {/* خطة Enterprise */}
        <div className={`card border-2 ${currentPlan === 'ENTERPRISE' ? 'border-primary-500' : 'border-gray-200'}`}>
          <h2 className="text-lg font-semibold">Enterprise</h2>
          <p className="text-3xl font-bold mt-2">مخصص</p>
          <ul className="mt-4 space-y-2 text-sm text-gray-600">
            <li className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-500" /> كل ميزات Pro</li>
            <li className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-500" /> دعم مخصص</li>
            <li className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-500" /> تكامل API</li>
          </ul>
          {currentPlan === 'ENTERPRISE' ? (
            <p className="mt-4 text-primary-600 font-medium">خطتك الحالية</p>
          ) : (
            <button onClick={() => handleUpgrade('ENTERPRISE')} disabled={loading} className="btn-primary w-full mt-4">
              <CreditCard className="w-4 h-4 ml-1" /> تواصل معنا
            </button>
          )}
        </div>
      </div>
    </div>
  );
}