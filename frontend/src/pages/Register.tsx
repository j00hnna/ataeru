import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { UserPlus, Mail, Lock, Building2, FileText, Hash, AlertCircle } from 'lucide-react';
import { AxiosError } from 'axios';

export default function Register() {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    company_name: '',
    commercial_register: '',
    tax_number: '',
  });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await register({
        full_name: formData.full_name,
        email: formData.email,
        password: formData.password,
        company_name: formData.company_name,
        commercial_register: formData.commercial_register || undefined,
        tax_number: formData.tax_number || undefined,
      });
      navigate('/dashboard');
    } catch (err) {
      if (err instanceof AxiosError && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('حدث خطأ أثناء إنشاء الحساب. يرجى المحاولة مرة أخرى.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-primary-50 to-white">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl mb-4">
            <span className="text-white font-bold text-3xl">A</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">إنشاء حساب جديد</h1>
          <p className="text-gray-500 mt-2">انضم إلى Ataeru وابدأ بالفوز بالمزيد من العطاءات</p>
        </div>

        <div className="card">
          {error && (
            <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* معلومات المستخدم */}
            <div className="border-b border-gray-200 pb-5 mb-2">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">معلومات المستخدم</h2>
              <div className="space-y-4">
                <div>
                  <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1">
                    الاسم الكامل
                  </label>
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    value={formData.full_name}
                    onChange={handleChange}
                    required
                    className="input-field"
                    placeholder="محمد أحمد"
                  />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                    البريد الإلكتروني
                  </label>
                  <div className="relative">
                    <Mail className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="email"
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      className="input-field pr-10"
                      placeholder="example@company.com"
                      dir="ltr"
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                    كلمة المرور
                  </label>
                  <div className="relative">
                    <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="password"
                      name="password"
                      type="password"
                      value={formData.password}
                      onChange={handleChange}
                      required
                      minLength={8}
                      className="input-field pr-10"
                      placeholder="•••••••• (8 أحرف على الأقل، حروف وأرقام)"
                      dir="ltr"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* معلومات الشركة */}
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-4">معلومات الشركة</h2>
              <div className="space-y-4">
                <div>
                  <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-1">
                    اسم الشركة <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Building2 className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="company_name"
                      name="company_name"
                      type="text"
                      value={formData.company_name}
                      onChange={handleChange}
                      required
                      className="input-field pr-10"
                      placeholder="شركة الإنشاءات المتحدة"
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="commercial_register" className="block text-sm font-medium text-gray-700 mb-1">
                    السجل التجاري (اختياري)
                  </label>
                  <div className="relative">
                    <FileText className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="commercial_register"
                      name="commercial_register"
                      type="text"
                      value={formData.commercial_register}
                      onChange={handleChange}
                      className="input-field pr-10"
                      placeholder="رقم السجل التجاري"
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="tax_number" className="block text-sm font-medium text-gray-700 mb-1">
                    الرقم الضريبي (اختياري)
                  </label>
                  <div className="relative">
                    <Hash className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="tax_number"
                      name="tax_number"
                      type="text"
                      value={formData.tax_number}
                      onChange={handleChange}
                      className="input-field pr-10"
                      placeholder="رقم التسجيل الضريبي"
                    />
                  </div>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary w-full flex items-center justify-center gap-2 mt-6"
            >
              <UserPlus className="w-5 h-5" />
              {isSubmitting ? 'جاري إنشاء الحساب...' : 'إنشاء الحساب'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-600">
            لديك حساب بالفعل؟{' '}
            <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">
              تسجيل الدخول
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}