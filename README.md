# Feedback Pulse Backend

FastAPI backend cho sản phẩm phân tích phản hồi sinh viên kiểu EduPulse.

## Chạy local

```bash
cd /Users/vietannguyen/myproject/ai_agent_generalization/paper-write-ai/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Ví dụ local trong tài liệu này dùng `http://127.0.0.1:8082`.

## Auth + Database

Backend hiện có:

- `register / login / logout`
- `me / profile update`
- hash password bằng `pbkdf2_sha256`
- session bằng `JWT` lưu trong `HttpOnly cookie`
- auto-create bảng `users` khi app startup

Tạo file `.env` từ `.env.example` rồi điền biến kết nối Postgres và auth secret:

```bash
cp .env.example .env
```

Các biến quan trọng:

```bash
POSTGRES_HOST=
POSTGRES_PORT=6543
POSTGRES_DB=postgres
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_SSLMODE=require

JWT_SECRET=
AUTH_COOKIE_SECURE=false
```

Nếu bạn muốn dùng đúng Supabase pooler, backend sẽ tự build `DATABASE_URL` từ các biến `POSTGRES_*`.

Lưu ý bảo mật:

- Không commit `.env`
- Sau khi chia sẻ credentials trong chat, nên rotate lại password/secret thật ở môi trường thật

## Cấu hình sentiment bằng provider

Backend hiện hỗ trợ 3 nhánh sentiment:

- `rule_based`: heuristic cũ, chạy nhanh, không phụ thuộc model ngoài
- `openai`: `pandas + OpenAI Python SDK + fine-tuned GPT-4o-mini`
- `trained_model`: model sklearn pipeline lưu trong file `.pkl`

### OpenAI

```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_SENTIMENT_MODEL="ft:gpt-4o-mini-2024-07-18:personal::Cje33mEn"
export SENTIMENT_PROVIDER="openai"
```

Tuỳ chọn:

```bash
export SHOW_LABEL_PROGRESS="true"
```

### Trained Model

Model `.pkl` hiện được map theo convention VSFC trong repo:

- `0 = negative`
- `1 = neutral`
- `2 = positive`

Chạy với provider `trained_model`:

```bash
export SENTIMENT_PROVIDER="trained_model"
export TRAINED_MODEL_SENTIMENT_MODEL_PATH="/Users/vietannguyen/myproject/ai_agent_generalization/paper-write-ai/backend/model/vsfc_tfidf_svm_pipeline.pkl"
```

### Rule-based

Nếu cần quay về heuristic cũ để debug local:

```bash
export SENTIMENT_PROVIDER="rule_based"
```

## Endpoint chính

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `PATCH /api/auth/profile`
- `GET /api/sample-status`
- `GET /api/analyze-sample`
- `POST /api/analyze`

## Ghi chú

- Có thể cấu hình workbook mẫu qua biến môi trường `SAMPLE_WORKBOOK_PATH`.
- Backend này tái sử dụng parser workbook đã được kiểm tra với file `TongHopYKien_Hocky2,nam2022-2023.xlsx`.
- Để giảm số lần gọi API, backend chỉ label các comment duy nhất theo `comment_key`, sau đó map kết quả ngược lại cho toàn bộ records.
