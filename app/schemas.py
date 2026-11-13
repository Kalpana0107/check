from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# --- User Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "student"  # "teacher" or "student"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# --- Question Schemas ---
class QuestionCreate(BaseModel):
    question_number: int
    question_text: str
    chapter_tag: str
    max_marks: float = 5.0
    model_answer: str
    rubric_guidelines: Optional[str] = ""

class QuestionOut(BaseModel):
    id: int
    exam_id: int
    question_number: int
    question_text: str
    chapter_tag: str
    max_marks: float
    model_answer: str
    rubric_guidelines: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Exam Schemas ---
class ExamCreate(BaseModel):
    subject: str
    title: str
    description: Optional[str] = ""
    questions: List[QuestionCreate]

class ExamOut(BaseModel):
    id: int
    teacher_id: int
    subject: str
    title: str
    description: Optional[str]
    total_marks: float
    rubric_file_path: Optional[str]
    status: str
    created_at: datetime
    questions_count: Optional[int] = 0
    submissions_count: Optional[int] = 0

    class Config:
        from_attributes = True

class ExamDetailOut(ExamOut):
    questions: List[QuestionOut]
    teacher_name: Optional[str] = None

# --- Evaluation Schemas ---
class EvaluationResultOut(BaseModel):
    id: int
    submission_id: int
    question_id: Optional[int]
    question_number: int
    chapter_tag: str
    student_extracted_text: Optional[str]
    marks_awarded: float
    ai_suggested_marks: float
    max_marks: float
    conceptual_feedback: str
    improvement_tip: Optional[str]
    teacher_adjusted: bool
    teacher_comment: Optional[str]
    model_answer: Optional[str] = None
    question_text: Optional[str] = None

    class Config:
        from_attributes = True

class MarkAdjustment(BaseModel):
    evaluation_id: int
    marks_awarded: float
    teacher_comment: Optional[str] = ""

class BatchMarkAdjustment(BaseModel):
    adjustments: List[MarkAdjustment]
    teacher_notes: Optional[str] = ""

# --- Submission Schemas ---
class SubmissionOut(BaseModel):
    id: int
    exam_id: int
    student_id: int
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    exam_title: Optional[str] = None
    subject: Optional[str] = None
    file_path: str
    file_name: str
    file_type: str
    status: str
    total_score: float
    max_score: float
    percentage: float
    teacher_notes: Optional[str]
    submitted_at: datetime
    graded_at: Optional[datetime]
    published_at: Optional[datetime]

    class Config:
        from_attributes = True

class SubmissionDetailOut(SubmissionOut):
    evaluations: List[EvaluationResultOut]

# --- Analytics Schemas ---
class ExamScorePoint(BaseModel):
    exam_id: int
    exam_title: str
    subject: str
    date: str
    score: float
    max_score: float
    percentage: float

class ChapterPerformance(BaseModel):
    chapter_tag: str
    subject: str
    total_marks_possible: float
    total_marks_earned: float
    percentage: float
    questions_count: int
    improvement_scope: float  # Marks lost
    priority_level: str  # "High", "Medium", "Good"
    recommended_action: str

class StudentAnalyticsOut(BaseModel):
    student_id: int
    student_name: str
    total_exams_taken: int
    average_score_pct: float
    score_trends: List[ExamScorePoint]
    chapter_breakdowns: List[ChapterPerformance]
    top_strengths: List[str]
    weak_areas: List[ChapterPerformance]
    personalized_tips: List[str]

