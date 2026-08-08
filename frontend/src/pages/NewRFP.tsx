import { useState, useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Loader2, AlertCircle, CheckCircle, Edit, Save, RefreshCw } from 'lucide-react';
import api from '@/services/api';
import toast from 'react-hot-toast';
import { RFPUploadResponse, RFPStatusResponse, AnalysisStatus } from '@/types';

const TERMINAL_STATUSES: AnalysisStatus[] = ['completed', 'partially_completed', 'failed', 'needs_review'];

const QUALITY_LABELS: Record<string, string> = {
  excellent: 'ممتازة',
  good: 'جيدة',
  acceptable: 'مقبولة',
  poor: 'ضعيفة',
  failed: 'فشل',
};

export default function NewRFP() {
  const [analysisId, setAnalysisId] = useState<number | null>(null);
  const [status, setStatus] = useState<RFPStatusResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editedResult, setEditedResult] = useState<any>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setPolling(false);
  }, []);

  const fetchStatus = useCallback(async (id: number) => {
    try {
      const response = await api.get<RFPStatusResponse>(`/rfp/status/${id}`);
      setStatus(response.data);
      if (TERMINAL_STATUSES.includes(response.data.status)) {
        stopPolling();
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل تحميل الحالة');
      stopPolling();
    }
  }, [stopPolling]);

  useEffect(() => {
    if (polling && analysisId) {
      pollRef.current = setInterval(() => fetchStatus(analysisId), 3000);
    }
    return stopPolling;
  }, [polling, analysisId, fetchStatus, stopPolling]);

  // رفع ملف
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await api.post<RFPUploadResponse>('/rfp/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      toast.success('تم رفع العطاء وبدء التحليل في الخلفية');
      setAnalysisId(response.data.analysis_id);
      setStatus({
        id: response.data.analysis_id,
        status: response.data.status,
        quality_score: null,
        confidence_score: 0,
        progress: 0,
        retry_count: 0,
        attempt: 0,
        completed_at: null,
        error_message: null,
        result: null,
      });
      setPolling(true);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل الرفع');
    } finally {
      setIsUploading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
    disabled: isUploading || !!analysisId,
  });

  const handleSaveEdit = async () => {
    if (!analysisId || !editedResult) return;
    try {
      await api.put(`/rfp/${analysisId}`, {
        extracted_requirements: editedResult,
        mandatory_checklist: editedResult?.mandatory_requirements || [],
        evaluation_criteria: editedResult?.evaluation_criteria || {},
      });
      toast.success('تم حفظ التعديلات');
      setStatus(prev => prev ? { ...prev, result: editedResult } : prev);
      setEditMode(false);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل الحفظ');
    }
  };

  const renderRequirements = (result: any) => {
    if (!result) return null;
    return (
      <div className="space-y-6">
        {result.deadline && (
          <div className="card">
            <h3 className="font-semibold text-lg mb-2">📅 تاريخ التقديم النهائي</h3>
            <p className="text-xl text-primary-600">{result.deadline}</p>
          </div>
        )}

        {result.evaluation_criteria && Object.keys(result.evaluation_criteria).length > 0 && (
          <div className="card">
            <h3 className="font-semibold text-lg mb-3">⚖️ معايير التقييم</h3>
            {result.evaluation_criteria.technical_weight && (
              <p>الوزن الفني: {result.evaluation_criteria.technical_weight}%</p>
            )}
            {result.evaluation_criteria.price_weight && (
              <p>وزن السعر: {result.evaluation_criteria.price_weight}%</p>
            )}
          </div>
        )}

        {result.mandatory_requirements && result.mandatory_requirements.length > 0 && (
          <div className="card">
            <h3 className="font-semibold text-lg mb-3">✅ الشروط الإجبارية</h3>
            <ul className="space-y-2">
              {result.mandatory_requirements.map((item: any, idx: number) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-green-500 mt-1">•</span>
                  <span>{item.description}</span>
                  {item.is_mandatory && <span className="text-red-500 text-xs mr-2">(إجباري)</span>}
                </li>
              ))}
            </ul>
          </div>
        )}

        {result.technical_questions && result.technical_questions.length > 0 && (
          <div className="card">
            <h3 className="font-semibold text-lg mb-3">❓ الأسئلة الفنية</h3>
            <ol className="list-decimal list-inside space-y-2">
              {result.technical_questions.map((q: any, idx: number) => (
                <li key={idx}>{q.question}</li>
              ))}
            </ol>
          </div>
        )}

        {result.boq_summary && (
          <div className="card">
            <h3 className="font-semibold text-lg mb-3">📋 ملخص جدول الكميات</h3>
            {result.boq_summary.total_estimated_value && (
              <p>القيمة التقديرية: {result.boq_summary.total_estimated_value}</p>
            )}
            {Array.isArray(result.boq_summary.items) && (
              <ul className="space-y-1 text-sm">
                {result.boq_summary.items.map((item: any, idx: number) => (
                  <li key={idx}>• {item.description || item.name}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    );
  };

  const result = status?.result;
  const shownResult = editMode ? editedResult : result;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">عطاء جديد</h1>

      {!analysisId ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
            isDragActive ? 'border-primary-400 bg-primary-50' : 'border-gray-300 hover:border-primary-300'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          {isUploading ? (
            <div>
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary-600 mb-2" />
              <p className="text-gray-600">جاري رفع الملف...</p>
            </div>
          ) : (
            <div>
              <p className="text-xl text-gray-700 mb-2">اسحب وأفلت ملف العطاء هنا</p>
              <p className="text-gray-500">يدعم PDF و Word و Excel و TXT</p>
            </div>
          )}
        </div>
      ) : status?.status === 'queued' || status?.status === 'processing' ? (
        <div className="card text-center py-12">
          <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary-600 mb-4" />
          <h2 className="text-xl font-semibold mb-2">
            {status.status === 'queued' ? 'العطاء في قائمة الانتظار...' : 'جاري تحليل العطاء...'}
          </h2>
          <div className="space-y-2 text-gray-600 text-sm">
            <p>🤖 التحليل يتم في الخلفية دون إبطاء الخادم</p>
            {status.retry_count > 0 && (
              <p className="text-amber-600">⚠️ جارٍ إعادة المحاولة ({status.attempt})</p>
            )}
          </div>
          <div className="mt-6 max-w-md mx-auto">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>التقدم</span>
              <span>{status.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-primary-600 h-2.5 rounded-full transition-all"
                style={{ width: `${Math.max(status.progress, 4)}%` }}
              />
            </div>
          </div>
        </div>
      ) : status?.status === 'failed' ? (
        <div className="card text-center py-12">
          <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <h2 className="text-xl font-semibold text-red-600 mb-2">فشل التحليل</h2>
          <p className="text-gray-600 mb-2">{status.error_message || 'حدث خطأ غير معروف'}</p>
          <p className="text-xs text-gray-400 mb-4">
            المحاولات: {status.attempt} • درجة الثقة: {status.confidence_score}%
          </p>
          <button
            onClick={() => { setAnalysisId(null); setStatus(null); }}
            className="btn-primary mt-4 flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" /> محاولة جديدة
          </button>
        </div>
      ) : status?.status === 'partially_completed' || status?.status === 'needs_review' ? (
        <div>
          <div className="card border-amber-300 bg-amber-50 mb-6">
            <div className="flex items-center gap-2 text-amber-700 font-semibold">
              <AlertCircle className="w-5 h-5" />
              {status.status === 'needs_review' ? 'التحليل يحتاج إلى مراجعة بشرية' : 'اكتمل التحليل جزئياً'}
            </div>
            <p className="text-sm text-amber-600 mt-2">
              قد تكون بعض المعلومات ناقصة. راجع النتائج التالية وعدّلها يدوياً إن لزم.
            </p>
          </div>
          {renderRequirements(shownResult)}
          <div className="flex justify-end gap-2 mt-4">
            {editMode ? (
              <button onClick={handleSaveEdit} className="btn-primary flex items-center gap-1">
                <Save className="w-4 h-4" /> حفظ
              </button>
            ) : (
              <button onClick={() => setEditMode(true)} className="btn-secondary flex items-center gap-1">
                <Edit className="w-4 h-4" /> تعديل
              </button>
            )}
          </div>
        </div>
      ) : (
        /* مكتمل */
        <div>
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <CheckCircle className="text-green-500" /> تم التحليل بنجاح
            </h2>
            <div className="flex items-center gap-3">
              {status?.quality_score && (
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  status.quality_score === 'excellent' || status.quality_score === 'good'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-amber-100 text-amber-800'
                }`}>
                  الجودة: {QUALITY_LABELS[status.quality_score] || status.quality_score}
                </span>
              )}
              {status && status.confidence_score > 0 && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-700">
                  الثقة: {status.confidence_score}%
                </span>
              )}
              <div className="flex gap-2">
                {editMode ? (
                  <button onClick={handleSaveEdit} className="btn-primary flex items-center gap-1">
                    <Save className="w-4 h-4" /> حفظ
                  </button>
                ) : (
                  <button onClick={() => setEditMode(true)} className="btn-secondary flex items-center gap-1">
                    <Edit className="w-4 h-4" /> تعديل
                  </button>
                )}
              </div>
            </div>
          </div>

          {renderRequirements(shownResult)}
        </div>
      )}
    </div>
  );
}
