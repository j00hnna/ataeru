import { useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import api from '@/services/api';
import toast from 'react-hot-toast';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

interface ComplianceDetail {
  requirement_id: number;
  description: string;
  met: boolean;
  reasoning?: string;
}

interface ComplianceResult {
  id: number;
  compliance_score: number;
  compliance_details: ComplianceDetail[];
}

export default function ComplianceCheck() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const [searchParams] = useSearchParams();
  const [compliance, setCompliance] = useState<ComplianceResult | null>(null);
  const [runningCompliance, setRunningCompliance] = useState(false);

  const id = analysisId || searchParams.get('analysis_id') || '';

  const handleComplianceCheck = async () => {
    setRunningCompliance(true);
    try {
      const res = await api.post<ComplianceResult>(`/responses/compliance/${id}`);
      setCompliance(res.data);
      toast.success('اكتمل فحص الامتثال');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل فحص الامتثال');
    } finally {
      setRunningCompliance(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">فحص الامتثال</h1>

      {!id && <p className="text-gray-500">أدخل معرّف التحليل في المسار.</p>}

      {id && (
        <button
          onClick={handleComplianceCheck}
          disabled={runningCompliance}
          className="btn-secondary flex items-center gap-1"
        >
          {runningCompliance ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <CheckCircle className="w-4 h-4" />
          )}
          فحص الامتثال
        </button>
      )}

      {compliance && (
        <div className="mt-6 card">
          <h3 className="font-semibold text-lg">نتيجة الامتثال: {compliance.compliance_score}%</h3>
          <div className="mt-3 space-y-2">
            {compliance.compliance_details?.map((item) => (
              <div key={item.requirement_id} className="flex items-start gap-2 p-2 border rounded">
                {item.met ? (
                  <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                )}
                <div>
                  <p className="text-sm">{item.description}</p>
                  {!item.met && <p className="text-xs text-gray-500">{item.reasoning}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
