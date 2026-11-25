# HumanizedWord — Context-Preserving AI Text Humanizer

> **A high-performance, context-aware platform that transforms AI-generated text into fluent, human-sounding writing while mathematically guaranteeing preservation of facts, names, and original intent.**

---

## 🌟 Key Features

- **Fine-Tuned Small Language Model (SLM)**: Powered by a LoRA adapter on `Qwen/Qwen2.5-0.5B-Instruct`, capable of running fast and efficiently entirely on CPU (<1.5 GB RAM footprint).
- **5 Native Stylistic Tones**:
  - `General`: Balanced, natural human conversational tone (default).
  - `Academic`: Scholarly, rigorously structured academic register.
  - `Professional`: Polished, workplace and executive register.
  - `Friendly`: Warm, engaging, conversational style.
  - `Casual`: Relaxed, natural colloquial prose.
- **5-Dimensional Context Preservation (P4 Engine)**:
  - **Semantic Similarity** ($M_{sem} \ge 0.85$ via `all-MiniLM-L6-v2`)
  - **Named Entity Retention** ($M_{ner} = 1.0$ via spaCy `en_core_web_sm`)
  - **Keyword Locking** ($M_{kw} = 1.0$)
  - **Factual & Number Consistency** ($M_{fact}$)
  - **Intent & Modality Alignment** ($M_{intent}$)
- **Real-Time Visual Diff**: Highlights token-by-token insertions, deletions, and replacements.
- **Modern Next.js 14 Web Interface**: Distraction-free workspace with dark mode design system, tone pills, keyword locking chips, and score gauges.

---

## 📁 Repository Structure

```text
HumanizeWord_major/
├── backend/                       # FastAPI asynchronous REST backend
│   ├── app/                       # Application code (main, routers, pipeline, models)
│   ├── scripts/                   # Setup and verification scripts (setup_venv.ps1 / .sh)
│   ├── tests/                     # Pytest automated test suite
│   ├── requirements.txt           # Python dependencies
│   └── .env.example               # Backend environment template
├── frontend/                      # Next.js 14 + Tailwind CSS frontend
│   ├── src/                       # App Router, components, store, hooks
│   ├── package.json               # Node.js dependencies
│   └── .env.example               # Frontend environment template
├── kaggle_output/                 # Pre-trained fine-tuned model artifacts
│   └── output_qwen_0_5b/final_adapter/  # Qwen 2.5 LoRA weights & tokenizers
├── PROJECT_PROPOSAL_SYNOPSIS.md   # Unified Academic Capstone Proposal
└── README.md                      # This guide
```

---

## 🚀 Quickstart Guide for Teammates

### Prerequisites
- **Python 3.11** installed and added to `PATH`.
- **Node.js 18+** or **Node.js 20+** and `npm`.
- **PostgreSQL 14+** (Optional for local testing; default tests run via in-memory/mock fixtures).

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/<your-username>/HumanizeWord.git
cd HumanizeWord
```

---

### Step 2: Set Up Backend (FastAPI + PyTorch)

#### On Windows (PowerShell):
```powershell
cd backend

# Option A: Automatic setup script (re-creates .venv with pinned CPU stack)
.\scripts\setup_venv.ps1

# Option B: Manual setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

#### On Linux / macOS / WSL (Bash):
```bash
cd backend

# Option A: Automatic setup script
chmod +x scripts/setup_venv.sh
./scripts/setup_venv.sh

# Option B: Manual setup
python3 -m venv .venv
source .venv/bin/activate
pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

#### Configure Backend Environment:
```bash
# In backend directory:
cp .env.example .env
```
*(The default `.env` is already configured for local CPU inference and guest testing).*

#### Run Backend Server:
```bash
# Ensure your virtual environment is active:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API will be accessible at: `http://localhost:8000`
- Swagger / Interactive Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

---

### Step 3: Set Up Frontend (Next.js 14)

Open a new terminal window:

```bash
cd frontend

# Install Node dependencies
npm install

# Configure environment
cp .env.example .env.local

# Start development server
npm run dev
```

- Open your browser at: `http://localhost:3000`

---

### Step 4: Run Automated Tests

To ensure everything runs cleanly on your machine:

```bash
cd backend

# Run the full test suite
pytest

# Or run tests with verbose logging:
pytest -v tests/test_health.py tests/test_auth.py tests/test_humanize.py
```

---

## ⚙️ Environment Configuration

### Backend (`backend/.env`)
| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://humanize:humanize@localhost:5432/humanizedtext` | PostgreSQL connection string |
| `JWT_SECRET` | *(random string)* | Secret key for JWT signing |
| `BACKEND_URL` | `http://localhost:8000` | Backend host URL |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend client URL |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `HW_BASE_MODEL` | `Qwen/Qwen2.5-0.5B-Instruct` | Hugging Face base model identifier |
| `HW_ADAPTER_DIR` | `./kaggle_output/output_qwen_0_5b/final_adapter` | Path to fine-tuned LoRA adapter |
| `HW_PRELOAD_MODEL` | `1` | Preload weights on server startup |
| `HW_GUEST_LIMIT` | `6` | Max requests per hour for guest users |

### Frontend (`frontend/.env.local`)
| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |
| `NEXT_PUBLIC_SITE_URL` | `http://localhost:3000` | Frontend public domain |

---

## 👥 Contributors & Team

**Graphic Era Hill University, Bhimtal Campus**  
Department of Computer Science & Engineering (Session 2026–27)

- **Jagdish Chandra Bhatt** *(Team Leader)* — [GitHub Profile](https://github.com/gitbyjay25)
- **Saurabh Singh Bisht**
- **Rishant Bhatt**
- **Vijay Singh**

**Faculty Guide**: Mr. Rahul Singh *(Assistant Professor, Dept. of CSE)*
