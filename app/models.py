import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="student")  # 'teacher' or 'student'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    exams = relationship("Exam", back_populates="teacher", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="student", cascade="all, delete-orphan")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_marks = Column(Float, default=0.0)
    rubric_file_path = Column(String(500), nullable=True)
    status = Column(String(50), default="active")  # 'active', 'archived'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    teacher = relationship("User", back_populates="exams")
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan", order_by="Question.question_number")
    submissions = relationship("Submission", back_populates="exam", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    chapter_tag = Column(String(150), nullable=False)
    max_marks = Column(Float, nullable=False, default=5.0)
    model_answer = Column(Text, nullable=False)
    rubric_guidelines = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    exam = relationship("Exam", back_populates="questions")
    evaluations = relationship("EvaluationResult", back_populates="question", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")  # 'pending', 'evaluating', 'graded', 'published'
    total_score = Column(Float, default=0.0)
    max_score = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0)
    teacher_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    graded_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    exam = relationship("Exam", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    evaluations = relationship("EvaluationResult", back_populates="submission", cascade="all, delete-orphan", order_by="EvaluationResult.question_number")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    question_number = Column(Integer, nullable=False)
    chapter_tag = Column(String(150), nullable=False)
    student_extracted_text = Column(Text, nullable=True)
    marks_awarded = Column(Float, nullable=False, default=0.0)
    ai_suggested_marks = Column(Float, nullable=False, default=0.0)
    max_marks = Column(Float, nullable=False, default=5.0)
    conceptual_feedback = Column(Text, nullable=False)
    improvement_tip = Column(Text, nullable=True)
    teacher_adjusted = Column(Boolean, default=False)
    teacher_comment = Column(Text, nullable=True)

    # Relationships
    submission = relationship("Submission", back_populates="evaluations")
    question = relationship("Question", back_populates="evaluations")

