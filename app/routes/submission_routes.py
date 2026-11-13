import shutil
import uuid
import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Exam, Question, User, Submission, EvaluationResult
from app.schemas import (
    SubmissionOut, SubmissionDetailOut, EvaluationResultOut, BatchMarkAdjustment
)
from app.auth import get_current_user, get_current_teacher, get_current_student
from app.services.gemini_evaluator import gemini_evaluator
from app.config import settings

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])

@router.post("/upload", response_model=SubmissionOut)
async def upload_submission(
    exam_id: int = Form(...),
    file: UploadFile = File(...),
    auto_evaluate: bool = Form(True),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    file_ext = Path(file.filename).suffix.lower()
    allowed_exts = [".jpg", ".jpeg", ".png", ".pdf"]
    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Allowed file types are JPG, PNG, and PDF")

    unique_filename = f"student_{current_student.id}_exam_{exam.id}_{uuid.uuid4().hex[:8]}{file_ext}"
    saved_disk_path = settings.UPLOAD_DIR / unique_filename

    with open(saved_disk_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = f"/static/uploads/{unique_filename}"
    file_type = "application/pdf" if file_ext == ".pdf" else f"image/{file_ext.replace('.', '')}"

    submission = Submission(
        exam_id=exam.id,
        student_id=current_student.id,
        file_path=file_url,
        file_name=file.filename,
        file_type=file_type,
        status="pending",
        total_score=0.0,
        max_score=exam.total_marks,
        percentage=0.0
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # If auto_evaluate is True, execute AI conceptual grading immediately
    if auto_evaluate and exam.questions:
        await _run_ai_grading(submission, exam, saved_disk_path, db)
        db.refresh(submission)

    out = _format_submission_out(submission)
    return out

async def _run_ai_grading(submission: Submission, exam: Exam, file_disk_path: Path, db: Session):
    submission.status = "evaluating"
    db.commit()

    # Prepare question payload
    q_payload = []
    for q in exam.questions:
        q_payload.append({
            "id": q.id,
            "question_number": q.question_number,
            "chapter_tag": q.chapter_tag,
            "max_marks": q.max_marks,
            "question_text": q.question_text,
            "model_answer": q.model_answer,
            "rubric_guidelines": q.rubric_guidelines or ""
        })

    # Call Gemini Evaluator
    eval_result = await gemini_evaluator.evaluate_submission(
        file_path=str(file_disk_path),
        exam_title=exam.title,
        subject=exam.subject,
        questions=q_payload
    )

    # Delete existing evaluations if re-evaluating
    db.query(EvaluationResult).filter(EvaluationResult.submission_id == submission.id).delete()

    total_score = 0.0
    max_score = 0.0

    for ev_data in eval_result.get("evaluations", []):
        q_id = ev_data.get("question_id")
        if not q_id:
            # Match by question number
            matching_q = next((q for q in exam.questions if q.question_number == ev_data["question_number"]), None)
            q_id = matching_q.id if matching_q else None

        eval_record = EvaluationResult(
            submission_id=submission.id,
            question_id=q_id,
            question_number=ev_data["question_number"],
            chapter_tag=ev_data["chapter_tag"],
            student_extracted_text=ev_data.get("student_extracted_text", ""),
            marks_awarded=ev_data["marks_awarded"],
            ai_suggested_marks=ev_data["ai_suggested_marks"],
            max_marks=ev_data["max_marks"],
            conceptual_feedback=ev_data["conceptual_feedback"],
            improvement_tip=ev_data.get("improvement_tip", ""),
            teacher_adjusted=False
        )
        db.add(eval_record)
        total_score += ev_data["marks_awarded"]
        max_score += ev_data["max_marks"]

    submission.total_score = round(total_score, 1)
    submission.max_score = round(max_score, 1)
    submission.percentage = round((total_score / max_score * 100), 1) if max_score > 0 else 0.0
    submission.status = "graded"
    submission.graded_at = datetime.datetime.utcnow()
    submission.teacher_notes = eval_result.get("overall_summary", "Evaluation completed successfully.")
    db.commit()

@router.post("/{submission_id}/evaluate", response_model=SubmissionDetailOut)
async def trigger_evaluation(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    exam = submission.exam
    # Check permissions
    if current_user.role == "student" and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if current_user.role == "teacher" and exam.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    relative_file = submission.file_path.replace("/static/uploads/", "")
    file_disk_path = settings.UPLOAD_DIR / relative_file

    await _run_ai_grading(submission, exam, file_disk_path, db)
    db.refresh(submission)
    return _format_submission_detail(submission)

@router.get("/my", response_model=List[SubmissionOut])
def list_student_submissions(
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    submissions = (
        db.query(Submission)
        .filter(Submission.student_id == current_student.id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )
    return [_format_submission_out(s) for s in submissions]

@router.get("/queue", response_model=List[SubmissionOut])
def teacher_submission_queue(
    exam_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    query = db.query(Submission).join(Exam).filter(Exam.teacher_id == current_teacher.id)
    if exam_id:
        query = query.filter(Submission.exam_id == exam_id)
    if status_filter:
        query = query.filter(Submission.status == status_filter)

    submissions = query.order_by(Submission.submitted_at.desc()).all()
    return [_format_submission_out(s) for s in submissions]

@router.get("/{submission_id}", response_model=SubmissionDetailOut)
def get_submission_detail(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.role == "student":
        if submission.student_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        # If student and not yet published, status indicates grading in progress
    elif current_user.role == "teacher":
        if submission.exam.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

    return _format_submission_detail(submission)

@router.post("/{submission_id}/adjust-marks", response_model=SubmissionDetailOut)
def adjust_submission_marks(
    submission_id: int,
    payload: BatchMarkAdjustment,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission or submission.exam.teacher_id != current_teacher.id:
        raise HTTPException(status_code=404, detail="Submission not found or unauthorized")

    total_score = 0.0
    for adj in payload.adjustments:
        eval_record = db.query(EvaluationResult).filter(
            EvaluationResult.id == adj.evaluation_id,
            EvaluationResult.submission_id == submission_id
        ).first()
        if eval_record:
            # Bound marks between 0 and max_marks
            new_mark = max(0.0, min(float(adj.marks_awarded), float(eval_record.max_marks)))
            eval_record.marks_awarded = round(new_mark, 1)
            eval_record.teacher_adjusted = True
            if adj.teacher_comment:
                eval_record.teacher_comment = adj.teacher_comment.strip()

    db.commit()

    # Recalculate total
    all_evals = db.query(EvaluationResult).filter(EvaluationResult.submission_id == submission_id).all()
    for ev in all_evals:
        total_score += ev.marks_awarded

    submission.total_score = round(total_score, 1)
    if submission.max_score > 0:
        submission.percentage = round((total_score / submission.max_score * 100), 1)
    if payload.teacher_notes:
        submission.teacher_notes = payload.teacher_notes.strip()

    db.commit()
    db.refresh(submission)
    return _format_submission_detail(submission)

@router.post("/{submission_id}/publish", response_model=SubmissionDetailOut)
def publish_submission_result(
    submission_id: int,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission or submission.exam.teacher_id != current_teacher.id:
        raise HTTPException(status_code=404, detail="Submission not found or unauthorized")

    submission.status = "published"
    submission.published_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(submission)
    return _format_submission_detail(submission)

def _format_submission_out(sub: Submission) -> SubmissionOut:
    out = SubmissionOut.model_validate(sub)
    out.student_name = sub.student.full_name if sub.student else "Student"
    out.student_email = sub.student.email if sub.student else ""
    out.exam_title = sub.exam.title if sub.exam else "Exam"
    out.subject = sub.exam.subject if sub.exam else ""
    return out

def _format_submission_detail(sub: Submission) -> SubmissionDetailOut:
    out = SubmissionDetailOut.model_validate(sub)
    out.student_name = sub.student.full_name if sub.student else "Student"
    out.student_email = sub.student.email if sub.student else ""
    out.exam_title = sub.exam.title if sub.exam else "Exam"
    out.subject = sub.exam.subject if sub.exam else ""

    evals_out = []
    for ev in sub.evaluations:
        item = EvaluationResultOut.model_validate(ev)
        if ev.question:
            item.question_text = ev.question.question_text
            item.model_answer = ev.question.model_answer
        evals_out.append(item)
    out.evaluations = evals_out
    return out

