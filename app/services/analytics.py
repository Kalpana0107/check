from typing import Dict, Any, List
from collections import defaultdict
from sqlalchemy.orm import Session

from app.models import Submission, EvaluationResult, Exam, User, Question

def calculate_student_analytics(student_id: int, db: Session) -> Dict[str, Any]:
    student = db.query(User).filter(User.id == student_id).first()
    student_name = student.full_name if student else "Student"

    # Fetch all graded or published submissions for this student
    submissions = (
        db.query(Submission)
        .filter(
            Submission.student_id == student_id,
            Submission.status.in_(["graded", "published"])
        )
        .order_by(Submission.submitted_at.asc())
        .all()
    )

    score_trends = []
    total_earned = 0.0
    total_possible = 0.0

    # Collect submission IDs
    submission_ids = [s.id for s in submissions]

    for sub in submissions:
        exam = sub.exam
        date_str = sub.submitted_at.strftime("%b %d, %Y") if sub.submitted_at else "Recent"
        score_trends.append({
            "exam_id": sub.exam_id,
            "exam_title": exam.title if exam else "Exam",
            "subject": exam.subject if exam else "General",
            "date": date_str,
            "score": round(sub.total_score, 1),
            "max_score": round(sub.max_score, 1),
            "percentage": round(sub.percentage, 1)
        })
        total_earned += sub.total_score
        total_possible += sub.max_score

    # Aggregate by chapter_tag across all evaluations
    chapter_stats = defaultdict(lambda: {
        "chapter_tag": "",
        "subject": "",
        "total_marks_possible": 0.0,
        "total_marks_earned": 0.0,
        "questions_count": 0
    })

    if submission_ids:
        evaluations = (
            db.query(EvaluationResult)
            .filter(EvaluationResult.submission_id.in_(submission_ids))
            .all()
        )
        for ev in evaluations:
            tag = ev.chapter_tag or "General Concepts"
            # Get subject if possible
            sub_obj = ev.submission
            subj = sub_obj.exam.subject if sub_obj and sub_obj.exam else "General"

            chapter_stats[tag]["chapter_tag"] = tag
            chapter_stats[tag]["subject"] = subj
            chapter_stats[tag]["total_marks_possible"] += ev.max_marks
            chapter_stats[tag]["total_marks_earned"] += ev.marks_awarded
            chapter_stats[tag]["questions_count"] += 1

    chapter_breakdowns = []
    for tag, stats in chapter_stats.items():
        possible = stats["total_marks_possible"]
        earned = stats["total_marks_earned"]
        lost = max(0.0, possible - earned)
        pct = round((earned / possible * 100), 1) if possible > 0 else 0.0

        if pct < 65:
            priority = "High Priority"
            rec = f"Review foundational theories and conceptual problem-solving in {tag}."
        elif pct < 85:
            priority = "Medium Priority"
            rec = f"Solid intuition; refine analytical rigor and secondary constraints in {tag}."
        else:
            priority = "Mastered"
            rec = f"Consistently strong comprehension in {tag}. Keep applying to advanced problems."

        chapter_breakdowns.append({
            "chapter_tag": tag,
            "subject": stats["subject"],
            "total_marks_possible": round(possible, 1),
            "total_marks_earned": round(earned, 1),
            "percentage": pct,
            "questions_count": stats["questions_count"],
            "improvement_scope": round(lost, 1),
            "priority_level": priority,
            "recommended_action": rec
        })

    # Sort chapter breakdowns by improvement scope (highest lost marks first)
    chapter_breakdowns.sort(key=lambda x: x["improvement_scope"], reverse=True)

    weak_areas = [c for c in chapter_breakdowns if c["percentage"] < 80]
    top_strengths = [c["chapter_tag"] for c in chapter_breakdowns if c["percentage"] >= 80]

    # Generate personalized recommendations
    personalized_tips = []
    if weak_areas:
        for w in weak_areas[:3]:
            personalized_tips.append(
                f"Target {w['chapter_tag']} ({w['subject']}): You have an improvement headroom of {w['improvement_scope']} marks ({w['percentage']}% accuracy). {w['recommended_action']}"
            )
    else:
        personalized_tips.append("Consistently outstanding conceptual performance across all tested chapters!")

    avg_score_pct = round((total_earned / total_possible * 100), 1) if total_possible > 0 else 0.0

    return {
        "student_id": student_id,
        "student_name": student_name,
        "total_exams_taken": len(submissions),
        "average_score_pct": avg_score_pct,
        "score_trends": score_trends,
        "chapter_breakdowns": chapter_breakdowns,
        "top_strengths": top_strengths,
        "weak_areas": weak_areas,
        "personalized_tips": personalized_tips
    }

def calculate_exam_class_analytics(exam_id: int, db: Session) -> Dict[str, Any]:
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return {}

    submissions = db.query(Submission).filter(
        Submission.exam_id == exam_id,
        Submission.status.in_(["graded", "published"])
    ).all()

    if not submissions:
        return {
            "exam_id": exam_id,
            "exam_title": exam.title,
            "submissions_count": 0,
            "average_score": 0.0,
            "highest_score": 0.0,
            "lowest_score": 0.0,
            "chapter_difficulties": []
        }

    scores = [s.total_score for s in submissions]
    avg_score = round(sum(scores) / len(scores), 1)
    high_score = round(max(scores), 1)
    low_score = round(min(scores), 1)

    # Chapter breakdown across the exam
    sub_ids = [s.id for s in submissions]
    evaluations = db.query(EvaluationResult).filter(EvaluationResult.submission_id.in_(sub_ids)).all()

    chapter_stats = defaultdict(lambda: {"earned": 0.0, "possible": 0.0, "count": 0})
    for ev in evaluations:
        tag = ev.chapter_tag or "General"
        chapter_stats[tag]["earned"] += ev.marks_awarded
        chapter_stats[tag]["possible"] += ev.max_marks
        chapter_stats[tag]["count"] += 1

    chapter_difficulties = []
    for tag, stats in chapter_stats.items():
        poss = stats["possible"]
        earn = stats["earned"]
        pct = round((earn / poss * 100), 1) if poss > 0 else 0.0
        chapter_difficulties.append({
            "chapter_tag": tag,
            "average_percentage": pct,
            "total_questions_evaluated": stats["count"],
            "difficulty_rating": "Challenging" if pct < 70 else ("Moderate" if pct < 85 else "Well-Grasped")
        })

    chapter_difficulties.sort(key=lambda x: x["average_percentage"])

    return {
        "exam_id": exam_id,
        "exam_title": exam.title,
        "submissions_count": len(submissions),
        "average_score": avg_score,
        "highest_score": high_score,
        "lowest_score": low_score,
        "chapter_difficulties": chapter_difficulties
    }

