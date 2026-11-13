from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import StudentAnalyticsOut
from app.auth import get_current_user, get_current_student, get_current_teacher
from app.services.analytics import calculate_student_analytics, calculate_exam_class_analytics

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/student", response_model=StudentAnalyticsOut)
def get_my_analytics(
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    return calculate_student_analytics(current_student.id, db)

@router.get("/student/{student_id}", response_model=StudentAnalyticsOut)
def get_student_analytics_for_teacher(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    return calculate_student_analytics(student_id, db)

@router.get("/exam/{exam_id}")
def get_exam_analytics(
    exam_id: int,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    analytics = calculate_exam_class_analytics(exam_id, db)
    if not analytics:
        raise HTTPException(status_code=404, detail="Exam not found")
    return analytics

