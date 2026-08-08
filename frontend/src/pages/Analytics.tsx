import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';
import { Loader2, TrendingUp, FileText, CheckCircle, Award } from 'lucide-react';

interface AnalyticsData {
  total_analyses: number;
  total_responses: number;
  avg_compliance: number;
  exported_responses: number;
}

export default function Analytics() {
  const { user } = useAuth();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await api.get<AnalyticsData>('/analytics');
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin" /></div>;
  }

  if (!data) return <p className="text-center text-gray-500 py-12">لا توجد بيانات.</p>;

  const chartData = [
    { name: 'العطاءات', value: data.total_analyses },
    { name: 'الردود المولدة', value: data.total_responses },
    { name: 'الردود المصدرة', value: data.exported_responses }
  ];

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b'];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">تحليلاتي</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center"><FileText className="w-6 h-6 text-blue-600" /></div>
          <div>
            <p className="text-sm text-gray-500">العطاءات المحللة</p>
            <p className="text-2xl font-bold">{data.total_analyses}</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center"><TrendingUp className="w-6 h-6 text-green-600" /></div>
          <div>
            <p className="text-sm text-gray-500">الردود المولدة</p>
            <p className="text-2xl font-bold">{data.total_responses}</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center"><CheckCircle className="w-6 h-6 text-purple-600" /></div>
          <div>
            <p className="text-sm text-gray-500">متوسط الامتثال</p>
            <p className="text-2xl font-bold">{data.avg_compliance}%</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center"><Award className="w-6 h-6 text-yellow-600" /></div>
          <div>
            <p className="text-sm text-gray-500">تم تصديرها</p>
            <p className="text-2xl font-bold">{data.exported_responses}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold mb-4">ملخص النشاط</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2 className="font-semibold mb-4">توزيع الحالات</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}