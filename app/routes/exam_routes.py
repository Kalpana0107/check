import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Exam, Question, User, Submission
from app.schemas import ExamOut, ExamDetailOut, ExamCreate
from app.auth import get_current_user, get_current_teacher
from app.config import settings

router = APIRouter(prefix="/api/exams", tags=["Exams"])

@router.get("/", response_model=List[ExamOut])
def list_exams(
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Exam)
    if subject:
        query = query.filter(Exam.subject.ilike(f"%{subject}%"))
    
    # Teachers see exams they created or all; students see all active exams
    if current_user.role == "teacher":
        exams = query.filter(Exam.teacher_id == current_user.id).order_by(Exam.created_at.desc()).all()
    else:
        exams = query.filter(Exam.status == "active").order_by(Exam.created_at.desc()).all()

    result = []
    for exam in exams:
        item = ExamOut.model_validate(exam)
        item.questions_count = len(exam.questions)
        item.submissions_count = len(exam.submissions)
        result.append(item)
    return result

@router.get("/all-active", response_model=List[ExamOut])
def list_all_active_exams(db: Session = Depends(get_db)):
    """Public/student list of active exams for submission dropdowns"""
    exams = db.query(Exam).filter(Exam.status == "active").order_by(Exam.created_at.desc()).all()
    result = []
    for exam in exams:
        item = ExamOut.model_validate(exam)
        item.questions_count = len(exam.questions)
        item.submissions_count = len(exam.submissions)
        result.append(item)
    return result

@router.get("/{exam_id}", response_model=ExamDetailOut)
def get_exam(exam_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    out = ExamDetailOut.model_validate(exam)
    out.questions_count = len(exam.questions)
    out.submissions_count = len(exam.submissions)
    out.teacher_name = exam.teacher.full_name if exam.teacher else "Instructor"
    return out

@router.post("/create", response_model=ExamDetailOut)
def create_exam(
    exam_in: ExamCreate,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    if not exam_in.questions:
        raise HTTPException(status_code=400, detail="An exam must have at least one question")

    total_marks = sum(q.max_marks for q in exam_in.questions)

    exam = Exam(
        teacher_id=current_teacher.id,
        subject=exam_in.subject.strip(),
        title=exam_in.title.strip(),
        description=exam_in.description.strip() if exam_in.description else "",
        total_marks=total_marks,
        status="active"
    )
    db.add(exam)
    db.flush()  # get exam.id

    for q_data in exam_in.questions:
        q = Question(
            exam_id=exam.id,
            question_number=q_data.question_number,
            question_text=q_data.question_text.strip(),
            chapter_tag=q_data.chapter_tag.strip(),
            max_marks=q_data.max_marks,
            model_answer=q_data.model_answer.strip(),
            rubric_guidelines=q_data.rubric_guidelines.strip() if q_data.rubric_guidelines else ""
        )
        db.add(q)

    db.commit()
    db.refresh(exam)

    out = ExamDetailOut.model_validate(exam)
    out.questions_count = len(exam.questions)
    out.submissions_count = 0
    out.teacher_name = current_teacher.full_name
    return out

@router.post("/{exam_id}/upload-rubric")
async def upload_exam_rubric(
    exam_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.teacher_id == current_teacher.id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found or unauthorized")

    file_ext = Path(file.filename).suffix
    unique_name = f"rubric_{exam.id}_{uuid.uuid4().hex[:8]}{file_ext}"
    dest_path = settings.UPLOAD_DIR / unique_name

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    exam.rubric_file_path = f"/static/uploads/{unique_name}"
    db.commit()

    return {"message": "Rubric uploaded successfully", "rubric_file_path": exam.rubric_file_path}

@router.delete("/{exam_id}")
def delete_exam(exam_id: int, db: Session = Depends(get_db), current_teacher: User = Depends(get_current_teacher)):
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.teacher_id == current_teacher.id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    db.delete(exam)
    db.commit()
    return {"message": "Exam deleted successfully"}

