import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { FileText, Loader2, RefreshCw, Download, Edit, Save, AlertCircle, CheckCircle } from 'lucide-react';
import api from '@/services/api';
import toast from 'react-hot-toast';

interface AnswerItem {
  question: string;
  answer: string;
}

interface ResponseData {
  id: number;
  analysis_id: number;
  generated_content: AnswerItem[];
  status: 'DRAFT' | 'REVIEWED' | 'EXPORTED';
  version: number;
  compliance_score?: number;
  compliance_details?: Array<{
    requirement_id: any;
    description: string;
    met: boolean;
    reasoning: string;
  }>;
}

export default function ResponseViewer() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const [response, setResponse] = useState<ResponseData | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [answers, setAnswers] = useState<AnswerItem[]>([]);
  const [editMode, setEditMode] = useState(false);
  const [editedAnswers, setEditedAnswers] = useState<AnswerItem[]>([]);
  const [regeneratingQuestions, setRegeneratingQuestions] = useState<Set<number>>(new Set());
  const [compliance, setCompliance] = useState<ResponseData | null>(null);
  const [runningCompliance, setRunningCompliance] = useState(false);

  const fetchData = async () => {
    try {
      const [analysisRes, responseRes] = await Promise.all([
        api.get(`/rfp/${analysisId}`),
        api.get(`/responses/${analysisId}`).catch(() => null)
      ]);
      setAnalysis(analysisRes.data);
      if (responseRes) {
        const resp = responseRes.data;
        const content = resp.generated_content;
        const parsedAnswers: AnswerItem[] = Array.isArray(content) ? content : [];
        resp.generated_content = parsedAnswers;
        setResponse(resp);
        setAnswers(parsedAnswers);
        setEditedAnswers(parsedAnswers.map(a => ({...a})));
        setCompliance(resp.compliance_details ? resp : null);
      }
    } catch (err) {
      toast.error('فشل تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (analysisId) fetchData(); }, [analysisId]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await api.post(`/responses/generate/${analysisId}`);
      const content = res.data.generated_content;
      const parsedAnswers: AnswerItem[] = Array.isArray(content) ? content : [];
      res.data.generated_content = parsedAnswers;
      setResponse(res.data);
      setAnswers(parsedAnswers);
      setEditedAnswers(parsedAnswers.map(a => ({...a})));
      toast.success('تم توليد الرد');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل توليد الرد');
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveEdit = async () => {
    try {
      await api.put(`/responses/${analysisId}`, { answers: editedAnswers });
      setAnswers(editedAnswers.map(a => ({...a})));
      if (response) response.generated_content = editedAnswers;
      setEditMode(false);
      toast.success('تم الحفظ');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل الحفظ');
    }
  };

  const handleRegenerateQuestion = async (index: number) => {
    setRegeneratingQuestions(prev => new Set(prev).add(index));
    try {
      const res = await api.post(`/responses/regenerate/${analysisId}/${index}`);
      const newAnswer = res.data.answer;
      const updated = [...editedAnswers];
      updated[index] = { ...updated[index], answer: newAnswer };
      setEditedAnswers(updated);
      await api.put(`/responses/${analysisId}`, { answers: updated });
      setAnswers(updated.map(a => ({...a})));
      if (response) response.generated_content = updated;
      toast.success('تمت إعادة التوليد');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل إعادة التوليد');
    } finally {
      setRegeneratingQuestions(prev => {
        const newSet = new Set(prev);
        newSet.delete(index);
        return newSet;
      });
    }
  };

  const handleExport = async () => {
    try {
      const res = await api.post(`/responses/export/${analysisId}?format=docx`, null, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `response_${analysisId}.docx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('تم التصدير');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل التصدير');
    }
  };

  const handleComplianceCheck = async () => {
    setRunningCompliance(true);
    try {
      const res = await api.post(`/responses/compliance/${analysisId}`);
      const content = res.data.generated_content;
      res.data.generated_content = Array.isArray(content) ? content : [];
      setCompliance(res.data);
      setResponse(res.data);
      toast.success('اكتمل فحص الامتثال');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل فحص الامتثال');
    } finally {
      setRunningCompliance(false);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin" /></div>;

  if (!analysis || analysis.status !== 'completed') {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">التحليل غير مكتمل</h2>
        <p className="text-gray-600">يجب اكتمال تحليل العطاء أولاً.</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">رد العطاء</h1>
          <p className="text-gray-500">{analysis.original_file_name}</p>
        </div>
        <div className="flex gap-2">
          {!response ? (
            <button onClick={handleGenerate} disabled={generating} className="btn-primary">
              {generating ? <Loader2 className="w-4 h-4 animate-spin ml-1" /> : <FileText className="w-4 h-4 ml-1" />}
              توليد الرد
            </button>
          ) : (
            <>
              {editMode ? (
                <button onClick={handleSaveEdit} className="btn-primary"><Save className="w-4 h-4 ml-1" /> حفظ</button>
              ) : (
                <button onClick={() => setEditMode(true)} className="btn-secondary"><Edit className="w-4 h-4 ml-1" /> تعديل</button>
              )}
              <button onClick={handleComplianceCheck} disabled={runningCompliance} className="btn-secondary">
                {runningCompliance ? <Loader2 className="w-4 h-4 animate-spin ml-1" /> : <CheckCircle className="w-4 h-4 ml-1" />}
                فحص الامتثال
              </button>
              <button onClick={handleExport} className="btn-secondary"><Download className="w-4 h-4 ml-1" /> تصدير Word</button>
            </>
          )}
        </div>
      </div>

      {generating && (
        <div className="card text-center py-8 mb-6"><Loader2 className="w-8 h-8 animate-spin mx-auto mb-3" /><p>جاري توليد الردود...</p></div>
      )}

      {compliance?.compliance_details && (
        <div className="mt-6 card mb-6">
          <h3 className="font-semibold text-lg mb-3">
            نتيجة الامتثال: <span className={compliance.compliance_score === 100 ? 'text-green-600' : 'text-red-600'}>{compliance.compliance_score}%</span>
          </h3>
          <div className="mt-3 space-y-2">
            {compliance.compliance_details.map((item: any) => (
              <div key={item.requirement_id} className="flex items-start gap-2 p-2 border rounded">
                {item.met ? <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" /> : <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />}
                <div><p className="text-sm">{item.description}</p>{!item.met && <p className="text-xs text-gray-500">{item.reasoning}</p>}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {answers.length > 0 && (
        <div className="space-y-6">
          {answers.map((item, idx) => (
            <div key={idx} className="card">
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-semibold text-lg">{item.question}</h3>
                <button onClick={() => handleRegenerateQuestion(idx)} disabled={regeneratingQuestions.has(idx)} className="text-sm text-primary-600 hover:underline flex items-center gap-1">
                  {regeneratingQuestions.has(idx) ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                  إعادة
                </button>
              </div>
              {editMode ? (
                <textarea
                  value={editedAnswers[idx]?.answer || ''}
                  onChange={(e) => {
                    const newEdited = [...editedAnswers];
                    newEdited[idx] = { ...newEdited[idx], answer: e.target.value };
                    setEditedAnswers(newEdited);
                  }}
                  className="w-full border rounded p-2 text-sm h-32"
                />
              ) : (
                <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">{item.answer}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}