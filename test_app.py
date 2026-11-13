import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_pipeline():
    print("--- 1. Testing Health Check ---")
    resp = client.get("/api/health")
    assert resp.status_code == 200, resp.text
    print("Health response:", resp.json())

    print("\n--- 2. Testing Auth: Teacher & Student Demo Login ---")
    teacher_login = client.post("/api/auth/demo-login/teacher")
    assert teacher_login.status_code == 200, teacher_login.text
    teacher_token = teacher_login.json()["access_token"]
    print("Teacher Login OK. Full Name:", teacher_login.json()["user"]["full_name"])

    student_login = client.post("/api/auth/demo-login/student")
    assert student_login.status_code == 200, student_login.text
    student_token = student_login.json()["access_token"]
    student_id = student_login.json()["user"]["id"]
    print("Student Login OK. Full Name:", student_login.json()["user"]["full_name"])

    print("\n--- 3. Testing Listing Exams ---")
    exams_resp = client.get("/api/exams/", headers={"Authorization": f"Bearer {teacher_token}"})
    assert exams_resp.status_code == 200, exams_resp.text
    exams = exams_resp.json()
    print(f"Found {len(exams)} exams in database.")
    assert len(exams) >= 1
    test_exam = exams[0]
    print(f"Test Exam: ID {test_exam['id']} - {test_exam['title']} ({test_exam['subject']})")

    print("\n--- 4. Testing Teacher Exam Creation ---")
    new_exam_payload = {
        "subject": "Chemistry",
        "title": "Thermodynamics in Chemical Reactions",
        "description": "Enthalpy, entropy, Gibbs free energy, and spontaneous equilibrium.",
        "questions": [
            {
                "question_number": 1,
                "chapter_tag": "Chemical Thermodynamics",
                "max_marks": 5.0,
                "question_text": "Derive the relationship between standard Gibbs free energy change Delta G_0 and equilibrium constant K.",
                "model_answer": "At equilibrium, Delta G = 0 and Q = K. Delta G = Delta G_0 + R*T*ln(Q) => 0 = Delta G_0 + R*T*ln(K) => Delta G_0 = -R*T*ln(K). Spontaneous if Delta G_0 < 0.",
                "rubric_guidelines": "Reward setting Delta G = 0 at equilibrium, Delta G formula, and algebraic solution."
            }
        ]
    }
    create_exam_resp = client.post("/api/exams/create", json=new_exam_payload, headers={"Authorization": f"Bearer {teacher_token}"})
    assert create_exam_resp.status_code == 200, create_exam_resp.text
    created_exam = create_exam_resp.json()
    print(f"Created Exam ID: {created_exam['id']} with {len(created_exam['questions'])} question.")

    print("\n--- 5. Testing Student Upload Paper & Multimodal AI Evaluation ---")
    # Upload simulated paper to the newly created exam
    files = {"file": ("student_chemistry_paper.png", open("app/static/uploads/sample_paper.png", "rb"), "image/png")}
    data = {"exam_id": created_exam["id"], "auto_evaluate": "true"}
    upload_resp = client.post("/api/submissions/upload", data=data, files=files, headers={"Authorization": f"Bearer {student_token}"})
    assert upload_resp.status_code == 200, upload_resp.text
    submission = upload_resp.json()
    sub_id = submission["id"]
    print(f"Uploaded Submission ID: {sub_id}, Status: {submission['status']}, Score: {submission['total_score']}/{submission['max_score']}")

    print("\n--- 6. Testing Teacher Review Queue & Submission Details ---")
    queue_resp = client.get("/api/submissions/queue", headers={"Authorization": f"Bearer {teacher_token}"})
    assert queue_resp.status_code == 200, queue_resp.text
    print(f"Teacher Review Queue has {len(queue_resp.json())} submissions.")

    detail_resp = client.get(f"/api/submissions/{sub_id}", headers={"Authorization": f"Bearer {teacher_token}"})
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    print(f"Submission detail has {len(detail['evaluations'])} evaluated questions.")
    ev1 = detail["evaluations"][0]
    print(f"Q1 Conceptual Feedback: {ev1['conceptual_feedback']}")
    print(f"Q1 Improvement Tip: {ev1['improvement_tip']}")

    print("\n--- 7. Testing Teacher Adjust Marks & Publish ---")
    adjust_payload = {
        "adjustments": [
            {
                "evaluation_id": ev1["id"],
                "marks_awarded": 4.8,
                "teacher_comment": "Excellent derivation, clearly stated equilibrium condition Delta G = 0."
            }
        ],
        "teacher_notes": "Well articulated chemistry logic."
    }
    adj_resp = client.post(f"/api/submissions/{sub_id}/adjust-marks", json=adjust_payload, headers={"Authorization": f"Bearer {teacher_token}"})
    assert adj_resp.status_code == 200, adj_resp.text
    adj_result = adj_resp.json()
    print(f"Adjusted Score: {adj_result['total_score']}/{adj_result['max_score']} ({adj_result['percentage']}%)")

    # Publish
    pub_resp = client.post(f"/api/submissions/{sub_id}/publish", headers={"Authorization": f"Bearer {teacher_token}"})
    assert pub_resp.status_code == 200, pub_resp.text
    assert pub_resp.json()["status"] == "published"
    print("Submission successfully published to student!")

    print("\n--- 8. Testing Student Report Card View ---")
    student_report = client.get(f"/api/submissions/{sub_id}", headers={"Authorization": f"Bearer {student_token}"})
    assert student_report.status_code == 200, student_report.text
    print("Student can view published report card with score:", student_report.json()["total_score"])

    print("\n--- 9. Testing Student Growth & Improvement Analytics ---")
    analytics_resp = client.get("/api/analytics/student", headers={"Authorization": f"Bearer {student_token}"})
    assert analytics_resp.status_code == 200, analytics_resp.text
    analytics = analytics_resp.json()
    print(f"Student Average Score: {analytics['average_score_pct']}% across {analytics['total_exams_taken']} exams.")
    print(f"Score trends count: {len(analytics['score_trends'])}")
    print(f"Chapters evaluated count: {len(analytics['chapter_breakdowns'])}")
    print(f"Top Strengths: {analytics['top_strengths']}")
    if analytics['weak_areas']:
        w = analytics['weak_areas'][0]
        print(f"Top Scope of Improvement Chapter: {w['chapter_tag']} (-{w['improvement_scope']} marks lost, Priority: {w['priority_level']})")
    print(f"Personalized pedagogical tips: {analytics['personalized_tips']}")

    print("\n--- 10. Testing HTML Frontend Pages ---")
    assert client.get("/").status_code == 200
    assert client.get("/teacher").status_code == 200
    assert client.get("/student").status_code == 200
    print("All frontend routes (/, /teacher, /student) returned HTTP 200 OK!")

    print("\nALL FULL-STACK TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_pipeline()

