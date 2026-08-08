# Ataeru - منصة تحليل العطاءات الذكية

منصة لتحليل وثائق العطاءات (RFP) بالذكاء الاصطناعي: استخراج المتطلبات، الأسئلة الفنية، الآجال، معالجة غير متزامنة، توليد الردود، وتدقيق الامتثال.

## متطلبات التشغيل
- Python 3.11+
- Node.js 20+
- Docker (لتشغيل PostgreSQL و Redis)
- مفتاح OpenAI API (اختياري — بدون المفتاح يعمل التطبيق بوضع المحاكاة)

## إعداد بيئة التطوير

### 1. تشغيل قواعد البيانات (PostgreSQL + Redis)
```bash
docker-compose up -d
```

### 2. تثبيت التبعيات الخلفية
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # للاختبارات
```

### 3. الإعدادات
```bash
cp .env.example .env
# عدّل القيم (SECRET_KEY، OPENAI_API_KEY، DATABASE_URL...)
```
> **وضع المحاكاة:** بدون `OPENAI_API_KEY` يتحول التطبيق تلقائياً إلى مزود وهمي
> (`AI_PROVIDER=mock`) يُكمل التحليل والردود ببيانات تجريبية — مثالي للتطوير.
> لتفعيل الذكاء الاصطناعي الحقيقي: ضع المفتاح واضبط `AI_PROVIDER=openai`.
> ملاحظة: RAG (قاعدة المعرفة) يتطلب `sentence-transformers` — بدونها تعمل بقية
> الميزات وتُرجع قاعدة المعرفة نتائج فارغة.

### 4. ترحيل قاعدة البيانات
```bash
cd backend
alembic upgrade head
```
> ملاحظة: إذا كانت لديك قاعدة بيانات قديمة من الإصدار السابق، احذفها وأعد إنشاءها مرة واحدة:
> `docker-compose down -v && docker-compose up -d && alembic upgrade head`

### 5. تشغيل التطبيق والعامل (Celery)
```bash
# التطبيق
cd backend
uvicorn app.main:app --reload

# عامل Celery (في محطة منفصلة)
celery -A celery_app worker -Q analysis -l info

# (اختياري) مراقبة مهام Celery عبر Flower
celery -A celery_app flower --port=5555
```

### 6. الواجهة الأمامية
```bash
cd frontend
npm install
npm run dev
```

## الاختبارات
```bash
cd backend
pytest
```
تغطي: التقسيم الذكي، جودة النتائج، API (رفع/حالة/قائمة)، مسار المعالجة الكامل
(مهمة Celery)، وتدفق الردود (توليد → امتثال → تصدير).

## نقاط النهاية الرئيسية
- `POST /api/v1/rfp/upload` — رفع ملف وبدء تحليل غير متزامن (202)
- `GET /api/v1/rfp/status/{id}` — حالة التحليل والتقدم والجودة
- `GET /api/v1/rfp/list` — قائمة التحليلات
- `GET /api/v1/rfp/{id}` — تفاصيل التحليل (مع Redis caching)
- `POST /api/v1/responses/generate/{analysis_id}` — توليد الرد
- `POST /api/v1/responses/compliance/{analysis_id}` — تدقيق الامتثال
- `POST /api/v1/responses/export/{analysis_id}?format=docx` — تصدير الرد

## هيكل المشروع
- backend/: FastAPI + SQLAlchemy + PostgreSQL + Redis + Celery
- backend/app/services/advanced_chunking.py: تقسيم ذكي للملفات الكبيرة
- backend/app/services/robust_rfp_service.py: التحليل القوي مع retry وجودة النتائج
- backend/app/services/ai_provider.py: مزود OpenAI مع وضع محاكاة تلقائي
- backend/celery_app.py: مهام Celery (analysis, exports)
- backend/alembic/: ترحيلات قاعدة البيانات
- frontend/: React 18 + TypeScript + Vite + Tailwind
- docker-compose.yml: PostgreSQL + Redis
