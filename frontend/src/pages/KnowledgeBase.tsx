import { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, CheckCircle, XCircle, Loader2, RefreshCw, Trash2 } from 'lucide-react';
import api from '@/services/api';
import { useAuth } from '@/hooks/useAuth';

interface KnowledgeDocument {
  id: number;
  file_name: string;
  file_url: string;
  file_type: string;
  status: 'UPLOADED' | 'PROCESSING' | 'READY' | 'FAILED';
  chunk_count: number;
  uploaded_at: string;
}

export default function KnowledgeBase() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const fetchDocuments = async () => {
    try {
      const response = await api.get<KnowledgeDocument[]>('/knowledge/documents');
      setDocuments(response.data);
    } catch (err) {
      console.error('فشل جلب المستندات', err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsUploading(true);
    setError('');
    for (const file of acceptedFiles) {
      const formData = new FormData();
      formData.append('file', file);
      try {
        await api.post('/knowledge/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      } catch (err: any) {
        setError(err.response?.data?.detail || 'فشل رفع الملف');
      }
    }
    setIsUploading(false);
    fetchDocuments();
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'image/*': ['.png', '.jpg', '.jpeg']
    },
    disabled: isUploading
  });

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const response = await api.get('/knowledge/search', {
        params: { query: searchQuery, top_k: 5 }
      });
      setSearchResults(response.data.results);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleReprocess = async (id: number) => {
    try {
      await api.post(`/knowledge/documents/${id}/process`);
      fetchDocuments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'فشلت إعادة المعالجة');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'UPLOADED':
      case 'PROCESSING':
        return <Loader2 className="w-5 h-5 text-yellow-500 animate-spin" />;
      case 'READY':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'FAILED':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'UPLOADED': return 'تم الرفع';
      case 'PROCESSING': return 'جاري المعالجة';
      case 'READY': return 'جاهز';
      case 'FAILED': return 'فشل';
      default: return status;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">قاعدة المعرفة</h1>
      <p className="text-gray-600 mb-8">
        ارفع ملفات شركتك (مشاريع سابقة، سير ذاتية، شهادات) لتصبح جزءاً من ذكاء المنصة.
      </p>

      {/* منطقة الرفع */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors mb-8 ${
          isDragActive ? 'border-primary-400 bg-primary-50' : 'border-gray-300 hover:border-primary-300'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-3" />
        {isUploading ? (
          <p className="text-gray-600">جاري رفع الملفات...</p>
        ) : isDragActive ? (
          <p className="text-primary-600">أفلت الملفات هنا</p>
        ) : (
          <div>
            <p className="text-gray-600">اسحب وأفلت الملفات هنا، أو انقر للاختيار</p>
            <p className="text-sm text-gray-400 mt-1">PDF، Word، صور (حتى 25 ميجابايت)</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* قائمة الملفات */}
      <div className="card mb-8">
        <h2 className="text-lg font-semibold mb-4">الملفات المرفوعة</h2>
        {documents.length === 0 ? (
          <p className="text-gray-400">لا توجد ملفات بعد.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-right border-b">
                  <th className="py-2 px-3">اسم الملف</th>
                  <th className="py-2 px-3">النوع</th>
                  <th className="py-2 px-3">الحالة</th>
                  <th className="py-2 px-3">الأجزاء</th>
                  <th className="py-2 px-3">التاريخ</th>
                  <th className="py-2 px-3">إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-400" />
                      {doc.file_name}
                    </td>
                    <td className="py-2 px-3">{doc.file_type}</td>
                    <td className="py-2 px-3 flex items-center gap-1">
                      {getStatusIcon(doc.status)}
                      <span className="text-xs">{getStatusText(doc.status)}</span>
                    </td>
                    <td className="py-2 px-3">{doc.chunk_count}</td>
                    <td className="py-2 px-3 text-xs text-gray-500">
                      {new Date(doc.uploaded_at).toLocaleDateString('ar-SA')}
                    </td>
                    <td className="py-2 px-3">
                      {doc.status === 'FAILED' && (
                        <button
                          onClick={() => handleReprocess(doc.id)}
                          className="text-primary-600 hover:underline text-xs flex items-center gap-1"
                        >
                          <RefreshCw className="w-3 h-3" /> إعادة
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* البحث الدلالي */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">بحث دلالي في المعرفة</h2>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="ابحث في محتوى الملفات..."
            className="input-field flex-1"
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch} disabled={isSearching} className="btn-primary">
            {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : 'بحث'}
          </button>
        </div>
        {searchResults.length > 0 && (
          <div className="space-y-2">
            {searchResults.map((res: any) => (
              <div key={res.chunk_id} className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-800">{res.text.substring(0, 200)}{res.text.length > 200 ? '...' : ''}</p>
                <span className="text-xs text-gray-400">مستند #{res.document_id} - جزء #{res.chunk_index}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}