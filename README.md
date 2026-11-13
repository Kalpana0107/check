# AutoGrade AI — Full-Stack Multimodal Exam Checking & Growth Analytics Platform

AutoGrade AI is an AI-powered online exam evaluation platform where teachers upload master answer keys with chapter-mapped rubrics, students upload photos/PDFs of their handwritten answer sheets, and a multimodal AI evaluates submissions based on **conceptual logic and meaning** (not just rote keyword matching), generating granular grading breakdowns and chapter-wise growth analytics.

---

## 🚀 Key Features

1. **Exact UI Aesthetic Preserved:**
   - Seamlessly preserves the original landing page's design theme, `#1d4ed8` / `#3b82f6` color palette, Tailwind CSS styling, FontAwesome icons, and Inter typography.
2. **Multimodal Conceptual AI Grading (Gemini 2.5 Flash / Pro):**
   - Transcribes student handwriting (equations, text, derivations) from scanned images/PDFs.
   - Evaluates the *underlying conceptual logic and principles*, awarding full credit for valid alternative derivations and intuitive reasoning even when textbook buzzwords vary.
   - Provides question-by-question feedback, identifying exact logical gaps and actionable pedagogical improvement tips.
   - Includes an automatic fallback simulation engine for offline or pre-API-key testing.
3. **Teacher Command Center (`/teacher`):**
   - **Exam & Rubric Creator:** Define exams with Subject, Title, Description, and dynamic question mapping (Question No., Chapter/Topic Tag, Max Marks, Model Concept Answer, Rubric Criteria).
   - **Submissions & Review Queue:** Inspect student answer papers side-by-side with OCR transcriptions and AI marks.
   - **Teacher-in-the-Loop Override:** Easily adjust marks per question, add teacher remarks, and click **Publish Results**.
   - **Class Diagnostics:** Identify which chapters the entire class found most challenging.
4. **Student Dashboard & Growth Analytics (`/student`):**
   - **Answer Paper Submission:** Upload scanned photos or PDF answer sheets with drag-and-drop.
   - **Evaluated Report Cards:** View score breakdowns, transcribed answers, comparison against teacher model logic, and AI conceptual critiques.
   - **Growth & Improvement Analytics:**
     - Interactive **Score Trends Chart** across exams over time per subject.
     - **Scope of Improvement Table** prioritizing weak chapters based on lost marks with pedagogical action plans.
     - **Personalized Recommendations** and strength mastery badges.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.14 + FastAPI + Pydantic v2 + Uvicorn
- **Database:** SQLite + SQLAlchemy ORM (models for `User`, `Exam`, `Question`, `Submission`, `EvaluationResult`)
- **Authentication:** JWT (python-jose) + Bcrypt with Teacher and Student roles + 1-Click Demo Logins
- **AI Engine:** Google Gemini API (`gemini-2.5-flash` / `gemini-2.5-pro` multimodal) via `httpx` with structured JSON output + intelligent fallback
- **Frontend:** Responsive HTML5 + Tailwind CSS + FontAwesome 6 + Chart.js for student analytics

---

## ⚡ Quick Start

### 1. Configure Environment (Optional for Live Gemini API)
Copy `.env.example` to `.env` and add your Google Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
SECRET_KEY=autograde-super-secret-jwt-key-2026
UPLOAD_DIR=app/static/uploads
DATABASE_URL=sqlite:///./autograde.db
```
*(Note: If no API key is provided, the platform automatically runs its built-in realistic conceptual evaluation simulation so you can test all features immediately.)*

### 2. Seed Demo Data
The workspace is pre-seeded with physics, cell biology, and computer science exams, student papers, and analytics:
```bash
python seed_data.py
```

### 3. Start the Server
```bash
python run.py
```
Or with uvicorn:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🔑 Demo Accounts

Use the **1-Click Instant Demo Login** buttons on the landing page or log in with:

| Role | Email | Password | Description |
| :--- | :--- | :--- | :--- |
| **Teacher** | `teacher@autograde.ai` | `teacher123` | Prof. Sarah Jenkins (manages exams & review queue) |
| **Student** | `alex@student.edu` | `student123` | Alex Chen (submits papers & views growth analytics) |
| **Student** | `priya@student.edu` | `student123` | Priya Sharma (physics paper in teacher review queue) |

---

## 📁 Project Structure

```
hackathon/
├── autograde_ai_prototype.html    # Original landing page prototype preserved
├── app/
│   ├── main.py                    # FastAPI application & static route mounting
│   ├── config.py                  # Environment settings & directory management
│   ├── database.py                # SQLite database session & engine
│   ├── models.py                  # SQLAlchemy models (User, Exam, Question, Submission, EvaluationResult)
│   ├── schemas.py                 # Pydantic schemas for requests/responses
│   ├── auth.py                    # JWT token creation & role security
│   ├── services/
│   │   ├── gemini_evaluator.py    # Multimodal OCR & conceptual grading logic
│   │   └── analytics.py           # Student growth trends & scope of improvement
│   ├── routes/
│   │   ├── auth_routes.py         # Login, signup, demo-login, system status
│   │   ├── exam_routes.py         # Teacher exam & rubric management
│   │   ├── submission_routes.py   # Student paper upload, AI grading, teacher adjustment & publish
│   │   └── analytics_routes.py    # Student growth & class diagnostics
│   ├── static/
│   │   ├── css/styles.css         # Styling, loaders, and toast notifications
│   │   ├── js/app.js              # Shared auth, fetch wrapper, toasts
│   │   ├── js/landing.js          # Landing page auth modals & prototype scanner
│   │   ├── js/teacher.js          # Teacher dashboard, review drawer, exam builder
│   │   ├── js/student.js          # Student dashboard, report cards, Chart.js trends
│   │   └── uploads/               # Uploaded answer sheets and sample paper
│   └── templates/
│       ├── index.html             # Upgraded landing page with auth & scanner
│       ├── teacher.html           # Full Teacher Command Center
│       └── student.html           # Student Dashboard & Report Cards
├── test_app.py                    # Comprehensive end-to-end test suite
├── seed_data.py                   # Realistic seed data script
├── run.py                         # Application runner
├── requirements.txt               # Dependencies
└── README.md
```

