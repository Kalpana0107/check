import os
import datetime
from sqlalchemy.orm import Session

from app.database import engine, Base, SessionLocal
from app.models import User, Exam, Question, Submission, EvaluationResult
from app.auth import hash_password

def seed():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        existing_teacher = db.query(User).filter(User.email == "teacher@autograde.ai").first()
        if existing_teacher:
            print("[Seed] Database already seeded. Skipping.")
            return

        print("[Seed] Seeding database with demo data...")

        # 1. Demo Users
        teacher = User(
            email="teacher@autograde.ai",
            password_hash=hash_password("teacher123"),
            full_name="Prof. Sarah Jenkins",
            role="teacher"
        )
        student_alex = User(
            email="alex@student.edu",
            password_hash=hash_password("student123"),
            full_name="Alex Chen",
            role="student"
        )
        student_priya = User(
            email="priya@student.edu",
            password_hash=hash_password("student123"),
            full_name="Priya Sharma",
            role="student"
        )
        student_marcus = User(
            email="marcus@student.edu",
            password_hash=hash_password("student123"),
            full_name="Marcus Vance",
            role="student"
        )

        db.add_all([teacher, student_alex, student_priya, student_marcus])
        db.flush()

        # 2. Physics Exam
        physics_exam = Exam(
            teacher_id=teacher.id,
            subject="Physics",
            title="Mid-Term Examination: Thermodynamics & Dynamics",
            description="Covers First/Second Laws of Thermodynamics, Adiabatic Processes, and Angular Momentum.",
            total_marks=20.0,
            status="active",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=14)
        )
        db.add(physics_exam)
        db.flush()

        pq1 = Question(
            exam_id=physics_exam.id,
            question_number=1,
            chapter_tag="Thermodynamics",
            question_text="Derive the relationship between work done and internal energy during an adiabatic process in an ideal gas. Explain why no heat transfer occurs.",
            max_marks=5.0,
            model_answer="In an adiabatic process, dQ = 0. By the First Law of Thermodynamics, dU = dQ - dW => dU = -dW. Work done by the system comes entirely at the expense of its internal energy: W = (P1*V1 - P2*V2) / (gamma - 1). The temperature drops if the gas expands adiabatically.",
            rubric_guidelines="Reward First Law application (dQ=0, dU=-dW), temperature change logic, and derivation of PV work."
        )
        pq2 = Question(
            exam_id=physics_exam.id,
            question_number=2,
            chapter_tag="Newtonian Dynamics",
            question_text="State the principle of conservation of angular momentum. Describe a real-world demonstration involving changing rotational inertia.",
            max_marks=5.0,
            model_answer="When the net external torque acting on a system is zero (tau_ext = 0), the total angular momentum L = I * omega remains constant. In a figure skater spinning with arms outstretched: pulling arms inward decreases rotational inertia (I), causing angular velocity (omega) to increase to conserve L.",
            rubric_guidelines="Must state condition of zero net external torque, formula L = I*omega, and clear mechanism of inertia reduction yielding speed increase."
        )
        pq3 = Question(
            exam_id=physics_exam.id,
            question_number=3,
            chapter_tag="Heat Engines & Entropy",
            question_text="Explain the Second Law of Thermodynamics in terms of entropy. Why cannot a heat engine achieve 100% thermal efficiency?",
            max_marks=5.0,
            model_answer="The Second Law states that for any spontaneous process, the total entropy of the universe increases: Delta S_universe >= 0. For a heat engine operating in a cyclic process, it must reject heat (Q_cold > 0) to a lower-temperature reservoir according to the Kelvin-Planck statement; hence thermal efficiency eta = 1 - (T_cold/T_hot) < 1.",
            rubric_guidelines="Check for Kelvin-Planck or Clausius reasoning, entropy change equation, and necessity of heat rejection reservoir."
        )
        pq4 = Question(
            exam_id=physics_exam.id,
            question_number=4,
            chapter_tag="Harmonic Motion",
            question_text="Distinguish between underdamped, critically damped, and overdamped oscillations with physical examples.",
            max_marks=5.0,
            model_answer="1. Underdamped (gamma < omega_0): System oscillates with exponentially decaying amplitude (e.g., plucked guitar string). 2. Critically Damped (gamma = omega_0): System returns to equilibrium in minimal time without oscillating (e.g., automobile shock absorbers). 3. Overdamped (gamma > omega_0): System slowly returns to equilibrium without oscillating (e.g., heavy hydraulic door closer).",
            rubric_guidelines="Award 1.5 marks for each regime definition with formula/criterion and 0.5 for physical examples."
        )
        db.add_all([pq1, pq2, pq3, pq4])
        db.flush()

        # 3. Biology Exam
        bio_exam = Exam(
            teacher_id=teacher.id,
            subject="Cell Biology",
            title="Unit Assessment: Bioenergetics & Molecular Genetics",
            description="Covers chemiosmotic phosphorylation, DNA replication enzymes, and Mendelian inheritance patterns.",
            total_marks=15.0,
            status="active",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=7)
        )
        db.add(bio_exam)
        db.flush()

        bq1 = Question(
            exam_id=bio_exam.id,
            question_number=1,
            chapter_tag="Cellular Respiration",
            question_text="Explain the chemiosmotic mechanism by which ATP is synthesized during oxidative phosphorylation across the inner mitochondrial membrane.",
            max_marks=5.0,
            model_answer="Protons (H+) are pumped from mitochondrial matrix into intermembrane space by Complexes I, III, and IV of the electron transport chain, creating an electrochemical proton gradient. Protons flow back into matrix through ATP Synthase (F0F1 complex), driving rotary catalytic phosphorylation of ADP + Pi into ATP.",
            rubric_guidelines="Must mention proton gradient / proton-motive force, intermembrane vs matrix locations, and ATP synthase rotary mechanism."
        )
        bq2 = Question(
            exam_id=bio_exam.id,
            question_number=2,
            chapter_tag="Molecular Genetics",
            question_text="Contrast the leading strand and lagging strand synthesis at the replication fork. Why are Okazaki fragments required?",
            max_marks=5.0,
            model_answer="DNA polymerases synthesize DNA exclusively in 5' to 3' direction. Because antiparallel parental strands open simultaneously: leading strand is synthesized continuously toward fork; lagging strand is oriented 3' to 5' relative to fork movement, requiring discontinuous synthesis of short Okazaki fragments each primed by RNA primase and sealed by DNA ligase.",
            rubric_guidelines="Reward 5'->3' enzyme constraint, continuous vs discontinuous explanation, and role of primase + DNA ligase."
        )
        bq3 = Question(
            exam_id=bio_exam.id,
            question_number=3,
            chapter_tag="Mendelian Genetics",
            question_text="Explain how incomplete dominance differs from codominance, providing an allele notation example for each.",
            max_marks=5.0,
            model_answer="Incomplete Dominance: Heterozygote exhibits an intermediate blended phenotype between homozygous traits (e.g., Red snapdragon CRCR x White CWCW -> Pink CRCW). Codominance: Both alleles are simultaneously and fully expressed in phenotype without blending (e.g., ABO blood type IAIB where both A and B glycoproteins are expressed on erythrocytes).",
            rubric_guidelines="Clear conceptual difference (blended intermediate vs dual distinct expression) with valid allele cross notations."
        )
        db.add_all([bq1, bq2, bq3])
        db.flush()

        # 4. Computer Science Exam
        cs_exam = Exam(
            teacher_id=teacher.id,
            subject="Computer Science",
            title="Quiz 3: Balanced Trees & Graph Search Algorithms",
            description="Algorithmic problem solving in graph traversal and self-balancing BST data structures.",
            total_marks=10.0,
            status="active",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=2)
        )
        db.add(cs_exam)
        db.flush()

        cq1 = Question(
            exam_id=cs_exam.id,
            question_number=1,
            chapter_tag="Binary Search Trees",
            question_text="Explain how AVL trees maintain O(log n) search time. Describe when a Left-Right (LR) double rotation is required.",
            max_marks=5.0,
            model_answer="An AVL tree maintains height balance where balance factor = |height(left) - height(right)| <= 1 for every node. A Left-Right rotation is required when a node is inserted into the right subtree of the left child (zig-zag pattern), requiring a left rotation on the child followed by a right rotation on the parent.",
            rubric_guidelines="Balance factor definition <= 1 and correct 2-step rotation sequence for zig-zag insertion."
        )
        cq2 = Question(
            exam_id=cs_exam.id,
            question_number=2,
            chapter_tag="Graph Theory",
            question_text="Why does Dijkstra's algorithm fail on graphs with negative weight edges? How does Bellman-Ford resolve this?",
            max_marks=5.0,
            model_answer="Dijkstra is a greedy algorithm assuming once a node is visited its shortest path is finalized. A negative weight edge visited later can invalidate this assumption. Bellman-Ford relaxes all |E| edges |V|-1 times, propagating negative improvements and detecting negative-weight cycles.",
            rubric_guidelines="Greedy finality assumption in Dijkstra vs |V|-1 relaxation cycles and cycle detection in Bellman-Ford."
        )
        db.add_all([cq1, cq2])
        db.flush()

        # 5. Alex Chen Physics Exam (Published with full breakdown)
        alex_sub_physics = Submission(
            exam_id=physics_exam.id,
            student_id=student_alex.id,
            file_path="/static/uploads/sample_paper.png",
            file_name="Alex_Physics_Midterm.png",
            file_type="image/png",
            status="published",
            total_score=17.5,
            max_score=20.0,
            percentage=87.5,
            teacher_notes="Well done Alex. Strong conceptual clarity on thermodynamics and dynamics. Review damped oscillations boundary values.",
            submitted_at=datetime.datetime.utcnow() - datetime.timedelta(days=10),
            graded_at=datetime.datetime.utcnow() - datetime.timedelta(days=9),
            published_at=datetime.datetime.utcnow() - datetime.timedelta(days=9)
        )
        db.add(alex_sub_physics)
        db.flush()

        e1 = EvaluationResult(
            submission_id=alex_sub_physics.id,
            question_id=pq1.id,
            question_number=1,
            chapter_tag="Thermodynamics",
            student_extracted_text="For adiabatic process, heat transfer dQ = 0. According to First Law: dU = dQ - dW. Since dQ = 0, dU = -dW. This means work done comes from internal energy. Therefore during expansion, temperature drops.",
            marks_awarded=5.0,
            ai_suggested_marks=5.0,
            max_marks=5.0,
            conceptual_feedback="Flawless conceptual reasoning! Student correctly derived dU = -dW and explained thermal energy conversion during expansion without missing any steps.",
            improvement_tip="Excellent work. You can explore polytropic processes P*V^n = C as a general case.",
            teacher_adjusted=False
        )
        e2 = EvaluationResult(
            submission_id=alex_sub_physics.id,
            question_id=pq2.id,
            question_number=2,
            chapter_tag="Newtonian Dynamics",
            student_extracted_text="Angular momentum is conserved when no external torque acts. L = I * w. Example: A rotating skater pulls arms inward. By decreasing radius, moment of inertia decreases, so rotational velocity w must increase to keep L constant.",
            marks_awarded=4.5,
            ai_suggested_marks=4.5,
            max_marks=5.0,
            conceptual_feedback="Clear physical reasoning and correct intuition on moment of inertia and angular velocity trade-off. Minor deduction: forgot to explicitly mention system boundary definition.",
            improvement_tip="Explicitly denote vector quantities (L_vec, tau_ext = 0) in formal derivations.",
            teacher_adjusted=False
        )
        e3 = EvaluationResult(
            submission_id=alex_sub_physics.id,
            question_id=pq3.id,
            question_number=3,
            chapter_tag="Heat Engines & Entropy",
            student_extracted_text="Entropy of the universe always increases: dS >= 0. A heat engine cannot be 100% efficient because it must reject heat into a cold sink. If it converted all heat into work without cold reservoir, Kelvin-Planck statement would be violated.",
            marks_awarded=4.5,
            ai_suggested_marks=4.5,
            max_marks=5.0,
            conceptual_feedback="Accurate application of the Second Law and Kelvin-Planck theorem. The explanation of why thermal rejection is physically mandatory is well articulated.",
            improvement_tip="Include the Carnot efficiency formula eta = 1 - (Tc/Th) to mathematically substantiate the limit.",
            teacher_adjusted=False
        )
        e4 = EvaluationResult(
            submission_id=alex_sub_physics.id,
            question_id=pq4.id,
            question_number=4,
            chapter_tag="Harmonic Motion",
            student_extracted_text="Underdamped: oscillates back and forth while getting smaller. Critically damped: stops fast without extra oscillations. Overdamped: takes a very long time to return.",
            marks_awarded=3.5,
            ai_suggested_marks=3.0,
            max_marks=5.0,
            conceptual_feedback="Conceptual descriptions are intuitive and correct, but omitted mathematical criteria (gamma vs omega_0) and practical engineering examples.",
            improvement_tip="Connect oscillatory behavior with damping ratio zeta and characteristic roots of the differential equation.",
            teacher_adjusted=True,
            teacher_comment="Bumped +0.5 for accurate qualitative understanding despite missing differential formulas."
        )
        db.add_all([e1, e2, e3, e4])

        # 6. Alex Chen Biology Exam Submission (Published)
        alex_sub_bio = Submission(
            exam_id=bio_exam.id,
            student_id=student_alex.id,
            file_path="/static/uploads/sample_paper.png",
            file_name="Alex_Biology_Assessment.png",
            file_type="image/png",
            status="published",
            total_score=11.5,
            max_score=15.0,
            percentage=76.7,
            teacher_notes="Good effort Alex. Focus on molecular details in Mendelian vs Non-Mendelian genetics.",
            submitted_at=datetime.datetime.utcnow() - datetime.timedelta(days=4),
            graded_at=datetime.datetime.utcnow() - datetime.timedelta(days=3),
            published_at=datetime.datetime.utcnow() - datetime.timedelta(days=3)
        )
        db.add(alex_sub_bio)
        db.flush()

        be1 = EvaluationResult(
            submission_id=alex_sub_bio.id,
            question_id=bq1.id,
            question_number=1,
            chapter_tag="Cellular Respiration",
            student_extracted_text="Complexes pump H+ from matrix into intermembrane space creating high concentration. Protons flow back through ATP synthase motor to create ATP from ADP and phosphate.",
            marks_awarded=4.5,
            ai_suggested_marks=4.5,
            max_marks=5.0,
            conceptual_feedback="Solid comprehension of proton-motive force and rotary catalysis in ATP synthase. Missing explicit mention of electrochemical potential terminology.",
            improvement_tip="Specify electrical and chemical concentration components of the proton gradient.",
            teacher_adjusted=False
        )
        be2 = EvaluationResult(
            submission_id=alex_sub_bio.id,
            question_id=bq2.id,
            question_number=2,
            chapter_tag="Molecular Genetics",
            student_extracted_text="DNA can only be made 5' to 3'. The leading strand goes toward the fork so it's continuous. The other strand goes backward in pieces called Okazaki fragments made with RNA primers and joined with ligase.",
            marks_awarded=4.5,
            ai_suggested_marks=4.5,
            max_marks=5.0,
            conceptual_feedback="Accurate grasp of directional limitation of DNA polymerase and necessity of discontinuous synthesis.",
            improvement_tip="Explain why RNA primers are required (DNA polymerase cannot initiate de novo).",
            teacher_adjusted=False
        )
        be3 = EvaluationResult(
            submission_id=alex_sub_bio.id,
            question_id=bq3.id,
            question_number=3,
            chapter_tag="Mendelian Genetics",
            student_extracted_text="Incomplete dominance is like pink flowers from red and white. Codominance is like blood types where both are seen. Both don't follow normal Mendel dominant/recessive rules.",
            marks_awarded=2.5,
            ai_suggested_marks=2.5,
            max_marks=5.0,
            conceptual_feedback="High-level idea is present, but lacked rigorous allele notations and molecular explanation of gene product dosage.",
            improvement_tip="Learn allele nomenclature (CRCR, CWCW, IAIB) and draw Punnett squares demonstrating phenotypic ratios.",
            teacher_adjusted=False
        )
        db.add_all([be1, be2, be3])

        # 7. Priya Sharma Submission for Review Queue (Graded, awaiting teacher review/publish)
        priya_sub = Submission(
            exam_id=physics_exam.id,
            student_id=student_priya.id,
            file_path="/static/uploads/sample_paper.png",
            file_name="Priya_Physics_Paper.png",
            file_type="image/png",
            status="graded",
            total_score=18.0,
            max_score=20.0,
            percentage=90.0,
            teacher_notes="AI Graded: Excellent conceptual understanding demonstrated across all physics topics.",
            submitted_at=datetime.datetime.utcnow() - datetime.timedelta(hours=5),
            graded_at=datetime.datetime.utcnow() - datetime.timedelta(hours=4)
        )
        db.add(priya_sub)
        db.flush()

        pe1 = EvaluationResult(
            submission_id=priya_sub.id,
            question_id=pq1.id,
            question_number=1,
            chapter_tag="Thermodynamics",
            student_extracted_text="In adiabatic process dQ = 0. By First Law dU = -dW. Gas expands against external pressure using thermal energy, leading to cooling.",
            marks_awarded=4.5,
            ai_suggested_marks=4.5,
            max_marks=5.0,
            conceptual_feedback="Very strong conceptual application. Derived dU = -dW correctly.",
            improvement_tip="Add integration limits P1V1 to P2V2.",
            teacher_adjusted=False
        )
        pe2 = EvaluationResult(
            submission_id=priya_sub.id,
            question_id=pq2.id,
            question_number=2,
            chapter_tag="Newtonian Dynamics",
            student_extracted_text="Total angular momentum L = I * omega is conserved when tau_ext = 0. When skater pulls limbs in, mass is closer to rotation axis, reducing I and increasing omega.",
            marks_awarded=5.0,
            ai_suggested_marks=5.0,
            max_marks=5.0,
            conceptual_feedback="Complete and rigorous derivation with clear physical analogy.",
            improvement_tip="Keep up the excellent mechanical intuition.",
            teacher_adjusted=False
        )
        pe3 = EvaluationResult(
            submission_id=priya_sub.id,
            question_id=pq3.id,
            question_number=3,
            chapter_tag="Heat Engines & Entropy",
            student_extracted_text="Second Law states dS_total >= 0. A cyclic heat engine cannot convert all heat Q_in into work without rejecting Q_out to a cold reservoir, otherwise entropy would decrease.",
            marks_awarded=4.5,
            ai_suggested_marks=4.5,
            max_marks=5.0,
            conceptual_feedback="Accurate entropy formulation and Kelvin-Planck theorem linkage.",
            improvement_tip="State Carnot theorem efficiency eta = 1 - Tc/Th.",
            teacher_adjusted=False
        )
        pe4 = EvaluationResult(
            submission_id=priya_sub.id,
            question_id=pq4.id,
            question_number=4,
            chapter_tag="Harmonic Motion",
            student_extracted_text="Underdamped: oscillates with decay (guitar string). Critically damped: returns to rest fastest (car shocks). Overdamped: returns sluggishly without oscillating (door closer).",
            marks_awarded=4.0,
            ai_suggested_marks=4.0,
            max_marks=5.0,
            conceptual_feedback="Correct regime classifications and high-quality real-world engineering examples.",
            improvement_tip="Review characteristic root formulas r = -gamma +- sqrt(gamma^2 - omega^2).",
            teacher_adjusted=False
        )
        db.add_all([pe1, pe2, pe3, pe4])

        db.commit()
        print("[Seed] Successfully seeded demo users, exams, questions, submissions, and evaluations!")

    except Exception as e:
        db.rollback()
        print(f"[Seed] Error seeding data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()

