// Teacher Dashboard Management Logic

let currentSubmissions = [];
let activeReviewSubmission = null;
let currentExams = [];

document.addEventListener('DOMContentLoaded', async () => {
    // Auth check
    const user = App.getUser();
    if (!user || user.role !== 'teacher') {
        App.showToast('Please sign in as a teacher', 'error');
        setTimeout(() => window.location.href = '/', 1000);
        return;
    }

    document.getElementById('teacher-name').textContent = user.full_name;
    document.getElementById('teacher-email').textContent = user.email;

    // Load initial data
    await loadTeacherStats();
    await loadSubmissionsQueue();
    await loadExamsList();
});

function switchTeacherTab(tabName) {
    const tabs = ['queue', 'exams', 'analytics'];
    tabs.forEach(t => {
        const pane = document.getElementById(`tab-pane-${t}`);
        const btn = document.getElementById(`nav-btn-${t}`);
        if (pane) {
            if (t === tabName) {
                pane.classList.remove('hidden');
                btn.classList.add('border-blue-600', 'text-blue-600');
                btn.classList.remove('border-transparent', 'text-slate-500');
            } else {
                pane.classList.add('hidden');
                btn.classList.remove('border-blue-600', 'text-blue-600');
                btn.classList.add('border-transparent', 'text-slate-500');
            }
        }
    });

    if (tabName === 'analytics') {
        loadClassAnalyticsTab();
    }
}

async function loadTeacherStats() {
    try {
        const exams = await App.apiFetch('/api/exams/');
        currentExams = exams;
        const queue = await App.apiFetch('/api/submissions/queue');
        currentSubmissions = queue;

        document.getElementById('stat-total-exams').textContent = exams.length;
        document.getElementById('stat-total-submissions').textContent = queue.length;
        
        const publishedCount = queue.filter(s => s.status === 'published').length;
        document.getElementById('stat-graded-count').textContent = publishedCount;

        const gradedOrPub = queue.filter(s => s.status === 'graded' || s.status === 'published');
        const avgScore = gradedOrPub.length > 0 
            ? Math.round(gradedOrPub.reduce((acc, s) => acc + s.percentage, 0) / gradedOrPub.length)
            : 0;
        document.getElementById('stat-avg-score').textContent = `${avgScore}%`;

    } catch (err) {
        console.error('Error loading stats:', err);
    }
}

// Submissions Queue
async function loadSubmissionsQueue() {
    const tableBody = document.getElementById('submissions-table-body');
    if (!tableBody) return;

    tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Loading submissions...</td></tr>`;

    try {
        const queue = await App.apiFetch('/api/submissions/queue');
        currentSubmissions = queue;

        if (queue.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-10 text-slate-500">No student submissions found. Active exams are open for student uploads.</td></tr>`;
            return;
        }

        tableBody.innerHTML = queue.map(sub => {
            const statusBadges = {
                'pending': '<span class="bg-amber-100 text-amber-800 text-xs px-2.5 py-1 rounded-full font-semibold">Pending AI</span>',
                'evaluating': '<span class="bg-blue-100 text-blue-800 text-xs px-2.5 py-1 rounded-full font-semibold"><i class="fa-solid fa-spinner fa-spin mr-1"></i>Evaluating</span>',
                'graded': '<span class="bg-purple-100 text-purple-800 text-xs px-2.5 py-1 rounded-full font-semibold">Graded (Review)</span>',
                'published': '<span class="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-1 rounded-full font-semibold"><i class="fa-solid fa-check mr-1"></i>Published</span>'
            };

            const dateStr = new Date(sub.submitted_at).toLocaleDateString(undefined, {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            });

            return `
                <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                    <td class="px-6 py-4">
                        <div class="font-bold text-slate-900">${sub.student_name}</div>
                        <div class="text-xs text-slate-400">${sub.student_email || ''}</div>
                    </td>
                    <td class="px-6 py-4">
                        <div class="font-medium text-slate-800">${sub.exam_title}</div>
                        <span class="inline-block bg-slate-100 text-slate-600 text-xs px-2 py-0.5 rounded font-medium">${sub.subject}</span>
                    </td>
                    <td class="px-6 py-4 text-xs text-slate-500">${dateStr}</td>
                    <td class="px-6 py-4">
                        ${sub.status === 'pending' || sub.status === 'evaluating' ? '<span class="text-slate-400 text-sm">--</span>' : `
                            <span class="font-bold text-slate-900">${sub.total_score}</span> <span class="text-xs text-slate-400">/ ${sub.max_score} (${sub.percentage}%)</span>
                        `}
                    </td>
                    <td class="px-6 py-4">${statusBadges[sub.status] || sub.status}</td>
                    <td class="px-6 py-4 text-right space-x-2">
                        ${sub.status === 'pending' ? `
                            <button onclick="triggerAiGrading(${sub.id})" class="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1.5 rounded-lg font-semibold transition shadow-sm">
                                <i class="fa-solid fa-microchip mr-1"></i> AI Grade
                            </button>
                        ` : `
                            <button onclick="openReviewModal(${sub.id})" class="bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 text-xs px-3 py-1.5 rounded-lg font-semibold transition border border-slate-200">
                                <i class="fa-solid fa-eye mr-1"></i> Review & Adjust
                            </button>
                        `}
                        ${sub.status === 'graded' ? `
                            <button onclick="publishResults(${sub.id})" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-3 py-1.5 rounded-lg font-semibold transition shadow-sm">
                                <i class="fa-solid fa-bullhorn mr-1"></i> Publish
                            </button>
                        ` : ''}
                    </td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-red-500">Failed to load submissions: ${err.message}</td></tr>`;
    }
}

async function triggerAiGrading(submissionId) {
    App.showToast('Evaluating paper with Gemini Multimodal AI...', 'info');
    try {
        await App.apiFetch(`/api/submissions/${submissionId}/evaluate`, { method: 'POST' });
        App.showToast('Evaluation complete! You can now review marks and conceptual feedback.', 'success');
        await loadSubmissionsQueue();
        await loadTeacherStats();
        openReviewModal(submissionId);
    } catch (err) {
        App.showToast(`Grading error: ${err.message}`, 'error');
    }
}

async function openReviewModal(submissionId) {
    const modal = document.getElementById('review-modal');
    modal.classList.remove('hidden');

    const content = document.getElementById('review-modal-content');
    content.innerHTML = `<div class="text-center py-16 text-slate-400"><i class="fa-solid fa-spinner fa-spin text-3xl mb-3 text-blue-600"></i><p>Loading submission & conceptual evaluation...</p></div>`;

    try {
        const sub = await App.apiFetch(`/api/submissions/${submissionId}`);
        activeReviewSubmission = sub;

        renderReviewModalContent(sub);
    } catch (err) {
        content.innerHTML = `<div class="p-8 text-center text-red-600">Error loading submission details: ${err.message}</div>`;
    }
}

function closeReviewModal() {
    const modal = document.getElementById('review-modal');
    modal.classList.add('hidden');
    activeReviewSubmission = null;
}

function renderReviewModalContent(sub) {
    const content = document.getElementById('review-modal-content');

    const evaluationsHtml = sub.evaluations.map(ev => {
        return `
            <div class="bg-slate-50 rounded-xl p-5 border border-slate-200 transition hover:border-blue-200">
                <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
                    <div class="flex items-center gap-2">
                        <span class="w-7 h-7 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center">Q${ev.question_number}</span>
                        <span class="text-xs bg-blue-100 text-blue-800 font-semibold px-2.5 py-0.5 rounded-full">${ev.chapter_tag}</span>
                        ${ev.teacher_adjusted ? '<span class="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-medium"><i class="fa-solid fa-pen mr-1"></i>Teacher Adjusted</span>' : ''}
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-slate-500 font-medium">AI Score: <strong>${ev.ai_suggested_marks}</strong></span>
                        <div class="flex items-center gap-1 bg-white px-2.5 py-1 rounded-lg border border-slate-300">
                            <label class="text-xs text-slate-600 font-semibold">Awarded:</label>
                            <input type="number" step="0.5" min="0" max="${ev.max_marks}" value="${ev.marks_awarded}" id="mark-input-${ev.id}" onchange="recalculateModalTotal()" class="w-14 text-center font-bold text-blue-600 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 rounded bg-slate-50 border border-slate-200">
                            <span class="text-xs text-slate-400">/ ${ev.max_marks}</span>
                        </div>
                    </div>
                </div>

                ${ev.question_text ? `
                    <div class="mb-3 text-xs bg-white p-3 rounded-lg border border-slate-100 text-slate-700">
                        <span class="font-semibold text-slate-900">Question:</span> ${ev.question_text}
                    </div>
                ` : ''}

                <div class="grid md:grid-cols-2 gap-4 mb-3 text-xs">
                    <div class="bg-white p-3 rounded-lg border border-slate-200">
                        <span class="font-bold text-slate-700 flex items-center gap-1 mb-1">
                            <i class="fa-solid fa-key text-blue-500"></i> Teacher's Model Concept Logic:
                        </span>
                        <p class="text-slate-600 leading-relaxed">${ev.model_answer || 'Standard rubric defined.'}</p>
                    </div>
                    <div class="bg-white p-3 rounded-lg border border-slate-200">
                        <span class="font-bold text-slate-700 flex items-center gap-1 mb-1">
                            <i class="fa-solid fa-pen-nib text-slate-500"></i> Student Answer (Transcribed via Multimodal OCR):
                        </span>
                        <p class="text-slate-600 leading-relaxed italic">${ev.student_extracted_text || 'Transcription pending'}</p>
                    </div>
                </div>

                <!-- AI Conceptual Reasoning -->
                <div class="bg-blue-50/60 rounded-lg p-3 text-xs border border-blue-100 mb-2">
                    <div class="font-bold text-blue-900 mb-1 flex items-center gap-1">
                        <i class="fa-solid fa-brain text-blue-600"></i> AI Conceptual Grading Logic:
                    </div>
                    <p class="text-slate-700 leading-relaxed">${ev.conceptual_feedback}</p>
                </div>

                ${ev.improvement_tip ? `
                    <div class="bg-amber-50/70 rounded-lg p-2.5 text-xs border border-amber-200/60 mb-2 flex items-start gap-2">
                        <i class="fa-solid fa-lightbulb text-amber-600 mt-0.5"></i>
                        <span class="text-amber-900"><strong>Targeted Growth Tip:</strong> ${ev.improvement_tip}</span>
                    </div>
                ` : ''}

                <div class="mt-2">
                    <input type="text" id="comment-input-${ev.id}" value="${ev.teacher_comment || ''}" placeholder="Optional teacher remark for this question..." class="w-full text-xs px-3 py-1.5 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500">
                </div>
            </div>
        `;
    }).join('');

    content.innerHTML = `
        <div class="space-y-6">
            <!-- Header bar inside modal -->
            <div class="flex flex-wrap items-center justify-between pb-4 border-b border-slate-100 gap-4">
                <div>
                    <h3 class="text-xl font-bold text-slate-900">${sub.exam_title}</h3>
                    <p class="text-xs text-slate-500">Student: <strong>${sub.student_name}</strong> &bull; Subject: ${sub.subject}</p>
                </div>
                <div class="flex items-center gap-4 bg-blue-50 px-4 py-2 rounded-xl border border-blue-100">
                    <div>
                        <div class="text-xs text-blue-700 font-medium">Calculated Score</div>
                        <div class="text-2xl font-black text-blue-700">
                            <span id="modal-total-score">${sub.total_score}</span> <span class="text-sm font-semibold text-blue-400">/ ${sub.max_score} (<span id="modal-total-pct">${sub.percentage}</span>%)</span>
                        </div>
                    </div>
                    <span class="bg-blue-600 text-white text-xs px-2.5 py-1 rounded-full font-bold uppercase">${sub.status}</span>
                </div>
            </div>

            <!-- Uploaded Paper Preview -->
            <div class="bg-slate-100 rounded-xl p-4 border border-slate-200">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold text-slate-700"><i class="fa-solid fa-file-image mr-1 text-blue-600"></i>Student's Uploaded Answer Paper</span>
                    <a href="${sub.file_path}" target="_blank" class="text-xs text-blue-600 hover:underline font-semibold flex items-center gap-1">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i> Open Full Paper
                    </a>
                </div>
                <div class="max-h-60 overflow-y-auto rounded-lg bg-white border border-slate-200 flex items-center justify-center p-2">
                    <img src="${sub.file_path}" alt="Uploaded Paper Preview" class="max-h-56 object-contain rounded shadow-sm" onerror="this.src='/static/uploads/sample_paper.png'">
                </div>
            </div>

            <!-- Question Breakdown List -->
            <div>
                <h4 class="font-bold text-slate-800 mb-3 text-sm flex items-center gap-2">
                    <i class="fa-solid fa-list-check text-blue-600"></i> Question & Conceptual Logic Evaluation Breakdown
                </h4>
                <div class="space-y-4">
                    ${evaluationsHtml}
                </div>
            </div>

            <!-- Overall Teacher Notes -->
            <div class="bg-white p-4 rounded-xl border border-slate-200">
                <label class="block text-xs font-bold text-slate-700 mb-1">Overall Feedback to Student</label>
                <textarea id="modal-teacher-notes" rows="2" class="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500">${sub.teacher_notes || ''}</textarea>
            </div>

            <!-- Action buttons -->
            <div class="flex flex-wrap items-center justify-between pt-4 border-t border-slate-100 gap-3">
                <button onclick="closeReviewModal()" class="px-5 py-2.5 rounded-xl border border-slate-200 text-slate-600 font-semibold text-xs hover:bg-slate-50 transition">
                    Close
                </button>
                <div class="flex items-center gap-3">
                    <button onclick="saveMarkAdjustments()" class="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-5 py-2.5 rounded-xl transition shadow-md flex items-center gap-2">
                        <i class="fa-solid fa-floppy-disk"></i> Save Adjustments
                    </button>
                    ${sub.status !== 'published' ? `
                        <button onclick="publishResults(${sub.id})" class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs px-5 py-2.5 rounded-xl transition shadow-md flex items-center gap-2">
                            <i class="fa-solid fa-bullhorn"></i> Publish Results
                        </button>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function recalculateModalTotal() {
    if (!activeReviewSubmission) return;
    let sum = 0;
    activeReviewSubmission.evaluations.forEach(ev => {
        const inp = document.getElementById(`mark-input-${ev.id}`);
        if (inp) {
            sum += parseFloat(inp.value) || 0;
        }
    });
    sum = Math.round(sum * 10) / 10;
    const max = activeReviewSubmission.max_score;
    const pct = max > 0 ? Math.round((sum / max) * 1000) / 10 : 0;

    const totalEl = document.getElementById('modal-total-score');
    const pctEl = document.getElementById('modal-total-pct');
    if (totalEl) totalEl.textContent = sum;
    if (pctEl) pctEl.textContent = pct;
}

async function saveMarkAdjustments() {
    if (!activeReviewSubmission) return;
    const adjustments = [];
    activeReviewSubmission.evaluations.forEach(ev => {
        const markInput = document.getElementById(`mark-input-${ev.id}`);
        const commentInput = document.getElementById(`comment-input-${ev.id}`);
        if (markInput) {
            adjustments.push({
                evaluation_id: ev.id,
                marks_awarded: parseFloat(markInput.value) || 0,
                teacher_comment: commentInput ? commentInput.value : ""
            });
        }
    });

    const teacherNotes = document.getElementById('modal-teacher-notes')?.value || "";

    try {
        const updated = await App.apiFetch(`/api/submissions/${activeReviewSubmission.id}/adjust-marks`, {
            method: 'POST',
            body: JSON.stringify({ adjustments, teacher_notes: teacherNotes })
        });
        App.showToast('Mark adjustments saved successfully!', 'success');
        activeReviewSubmission = updated;
        renderReviewModalContent(updated);
        await loadSubmissionsQueue();
        await loadTeacherStats();
    } catch (err) {
        App.showToast(`Error saving adjustments: ${err.message}`, 'error');
    }
}

async function publishResults(submissionId) {
    try {
        await App.apiFetch(`/api/submissions/${submissionId}/publish`, { method: 'POST' });
        App.showToast('Results published! The student can now view their evaluated report card.', 'success');
        closeReviewModal();
        await loadSubmissionsQueue();
        await loadTeacherStats();
    } catch (err) {
        App.showToast(`Failed to publish: ${err.message}`, 'error');
    }
}

// Exams list & creator
async function loadExamsList() {
    const container = document.getElementById('exams-list-container');
    if (!container) return;

    try {
        const exams = await App.apiFetch('/api/exams/');
        currentExams = exams;

        if (exams.length === 0) {
            container.innerHTML = `<div class="p-8 text-center text-slate-500 bg-white rounded-xl border border-slate-200">No exams created yet. Click "Create Exam & Master Key" above to get started.</div>`;
            return;
        }

        container.innerHTML = exams.map(e => `
            <div class="bg-white rounded-xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition">
                <div class="flex flex-wrap items-start justify-between gap-4 mb-4">
                    <div>
                        <span class="inline-block bg-blue-100 text-blue-700 text-xs px-2.5 py-0.5 rounded-full font-bold mb-2">${e.subject}</span>
                        <h3 class="text-xl font-bold text-slate-900">${e.title}</h3>
                        <p class="text-slate-500 text-xs mt-1 max-w-xl">${e.description || 'Master rubric configured.'}</p>
                    </div>
                    <div class="flex items-center gap-3">
                        <div class="text-right">
                            <div class="text-2xl font-black text-blue-600">${e.total_marks}</div>
                            <div class="text-xs text-slate-400 font-semibold uppercase">Total Marks</div>
                        </div>
                    </div>
                </div>

                <div class="flex flex-wrap items-center justify-between pt-4 border-t border-slate-100 text-xs text-slate-500 gap-4">
                    <div class="flex items-center gap-4">
                        <span><i class="fa-solid fa-list-ol mr-1 text-blue-500"></i><strong>${e.questions_count}</strong> Questions Mapped</span>
                        <span><i class="fa-solid fa-file-arrow-up mr-1 text-slate-400"></i><strong>${e.submissions_count}</strong> Submissions</span>
                    </div>
                    <div class="space-x-2">
                        <button onclick="viewExamDetails(${e.id})" class="text-blue-600 hover:text-blue-800 font-semibold px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 transition">
                            <i class="fa-solid fa-eye mr-1"></i> View Key & Questions
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-red-500">Failed to load exams: ${err.message}</div>`;
    }
}

// Create Exam Modal
let newExamQuestions = [];

function openCreateExamModal() {
    newExamQuestions = [
        {
            question_number: 1,
            chapter_tag: "",
            question_text: "",
            max_marks: 5,
            model_answer: "",
            rubric_guidelines: ""
        }
    ];
    renderQuestionBuilder();
    document.getElementById('create-exam-modal').classList.remove('hidden');
}

function closeCreateExamModal() {
    document.getElementById('create-exam-modal').classList.add('hidden');
}

function addQuestionToBuilder() {
    const nextNum = newExamQuestions.length + 1;
    newExamQuestions.push({
        question_number: nextNum,
        chapter_tag: "",
        question_text: "",
        max_marks: 5,
        model_answer: "",
        rubric_guidelines: ""
    });
    renderQuestionBuilder();
}

function removeQuestionFromBuilder(index) {
    if (newExamQuestions.length <= 1) {
        App.showToast('An exam must have at least one question', 'info');
        return;
    }
    newExamQuestions.splice(index, 1);
    // Renumber
    newExamQuestions.forEach((q, idx) => q.question_number = idx + 1);
    renderQuestionBuilder();
}

function renderQuestionBuilder() {
    const container = document.getElementById('questions-builder-container');
    if (!container) return;

    container.innerHTML = newExamQuestions.map((q, idx) => `
        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 relative mb-4">
            <div class="flex items-center justify-between mb-3">
                <span class="w-6 h-6 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center">Q${idx + 1}</span>
                <button type="button" onclick="removeQuestionFromBuilder(${idx})" class="text-slate-400 hover:text-red-500 text-xs">
                    <i class="fa-solid fa-trash"></i> Remove
                </button>
            </div>
            <div class="grid md:grid-cols-3 gap-3 mb-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Chapter / Topic Tag *</label>
                    <input type="text" value="${q.chapter_tag}" oninput="newExamQuestions[${idx}].chapter_tag = this.value" placeholder="e.g. Thermodynamics, Optics" required class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Max Marks *</label>
                    <input type="number" step="1" min="1" value="${q.max_marks}" oninput="newExamQuestions[${idx}].max_marks = parseFloat(this.value) || 1" required class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500">
                </div>
            </div>
            <div class="mb-3">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Question Prompt *</label>
                <textarea rows="2" oninput="newExamQuestions[${idx}].question_text = this.value" placeholder="State or derive..." required class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500">${q.question_text}</textarea>
            </div>
            <div class="mb-3">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Teacher's Model Answer / Core Concept Logic *</label>
                <textarea rows="2" oninput="newExamQuestions[${idx}].model_answer = this.value" placeholder="The conceptual steps, governing equations, causality..." required class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500">${q.model_answer}</textarea>
            </div>
            <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Rubric Grading Criteria & Acceptable Alternatives</label>
                <input type="text" value="${q.rubric_guidelines}" oninput="newExamQuestions[${idx}].rubric_guidelines = this.value" placeholder="Reward First Law application, accept alternative integral form..." class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500">
            </div>
        </div>
    `).join('');
}

async function handleCreateExamSubmit(event) {
    event.preventDefault();
    const subject = document.getElementById('exam-subject').value.trim();
    const title = document.getElementById('exam-title').value.trim();
    const description = document.getElementById('exam-description').value.trim();

    // Validate questions
    for (let i = 0; i < newExamQuestions.length; i++) {
        const q = newExamQuestions[i];
        if (!q.chapter_tag || !q.question_text || !q.model_answer) {
            App.showToast(`Please fill all required fields in Question ${i + 1}`, 'error');
            return;
        }
    }

    try {
        const payload = {
            subject,
            title,
            description,
            questions: newExamQuestions
        };

        const created = await App.apiFetch('/api/exams/create', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        App.showToast(`Exam "${created.title}" created with ${created.questions_count} questions!`, 'success');
        closeCreateExamModal();
        await loadExamsList();
        await loadTeacherStats();
    } catch (err) {
        App.showToast(`Failed to create exam: ${err.message}`, 'error');
    }
}

async function viewExamDetails(examId) {
    try {
        const exam = await App.apiFetch(`/api/exams/${examId}`);
        const modal = document.getElementById('review-modal');
        modal.classList.remove('hidden');

        const content = document.getElementById('review-modal-content');
        content.innerHTML = `
            <div class="space-y-6">
                <div class="flex items-center justify-between pb-4 border-b border-slate-100">
                    <div>
                        <span class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-bold">${exam.subject}</span>
                        <h3 class="text-2xl font-bold text-slate-900 mt-1">${exam.title}</h3>
                        <p class="text-slate-500 text-xs mt-1">${exam.description || 'Master Answer Key and Chapter Rubric'}</p>
                    </div>
                    <div class="text-right">
                        <div class="text-2xl font-black text-blue-600">${exam.total_marks}</div>
                        <div class="text-xs text-slate-400 font-semibold uppercase">Total Max Marks</div>
                    </div>
                </div>

                <div>
                    <h4 class="font-bold text-slate-800 text-sm mb-3">Model Answer Key & Chapter Mapping (${exam.questions.length} Questions)</h4>
                    <div class="space-y-4">
                        ${exam.questions.map(q => `
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200">
                                <div class="flex items-center justify-between mb-2">
                                    <div class="flex items-center gap-2">
                                        <span class="w-6 h-6 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center">Q${q.question_number}</span>
                                        <span class="text-xs bg-blue-100 text-blue-800 font-semibold px-2 py-0.5 rounded-full">${q.chapter_tag}</span>
                                    </div>
                                    <span class="text-xs font-bold text-slate-700 bg-white px-2 py-1 rounded border border-slate-200">${q.max_marks} Marks</span>
                                </div>
                                <div class="text-xs font-semibold text-slate-800 mb-2">${q.question_text}</div>
                                <div class="bg-white p-3 rounded-lg border border-slate-200 text-xs mb-2">
                                    <span class="font-bold text-blue-700"><i class="fa-solid fa-key mr-1"></i>Model Answer / Concept:</span>
                                    <p class="text-slate-600 mt-1 leading-relaxed">${q.model_answer}</p>
                                </div>
                                ${q.rubric_guidelines ? `
                                    <div class="text-xs text-slate-500 bg-slate-100/70 p-2 rounded">
                                        <span class="font-semibold text-slate-700">Grading Guidelines:</span> ${q.rubric_guidelines}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="flex justify-end pt-4 border-t border-slate-100">
                    <button onclick="closeReviewModal()" class="px-5 py-2.5 rounded-xl bg-blue-600 text-white font-semibold text-xs hover:bg-blue-700 transition">
                        Done
                    </button>
                </div>
            </div>
        `;
    } catch (err) {
        App.showToast(`Error: ${err.message}`, 'error');
    }
}

// Class Analytics Tab
async function loadClassAnalyticsTab() {
    const container = document.getElementById('class-analytics-content');
    if (!container) return;

    if (currentExams.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-slate-500">No exams available to analyze.</div>`;
        return;
    }

    const firstExamId = currentExams[0].id;
    try {
        const analytics = await App.apiFetch(`/api/analytics/exam/${firstExamId}`);
        renderExamAnalyticsView(analytics);
    } catch (err) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">Error loading class diagnostics: ${err.message}</div>`;
    }
}

function renderExamAnalyticsView(data) {
    const container = document.getElementById('class-analytics-content');
    if (!container) return;

    container.innerHTML = `
        <div class="bg-white rounded-xl p-6 border border-slate-200 shadow-sm mb-6">
            <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
                <div>
                    <h3 class="text-xl font-bold text-slate-900">${data.exam_title}</h3>
                    <p class="text-xs text-slate-500">Class Diagnostics & Chapter Difficulties</p>
                </div>
                <div class="flex items-center gap-6">
                    <div class="text-center">
                        <div class="text-2xl font-black text-blue-600">${data.average_score}</div>
                        <div class="text-xs text-slate-400 font-semibold uppercase">Class Average</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-black text-emerald-600">${data.highest_score}</div>
                        <div class="text-xs text-slate-400 font-semibold uppercase">Highest</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-black text-amber-600">${data.lowest_score}</div>
                        <div class="text-xs text-slate-400 font-semibold uppercase">Lowest</div>
                    </div>
                </div>
            </div>

            <h4 class="font-bold text-slate-800 text-sm mb-3">Chapter Difficulty Breakdown</h4>
            <div class="space-y-3">
                ${data.chapter_difficulties.map(cd => `
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <div class="font-bold text-slate-900 text-sm">${cd.chapter_tag}</div>
                            <div class="text-xs text-slate-500">${cd.total_questions_evaluated} responses evaluated</div>
                        </div>
                        <div class="flex items-center gap-4">
                            <div class="w-40 bg-slate-200 rounded-full h-2.5 overflow-hidden">
                                <div class="bg-blue-600 h-2.5 rounded-full" style="width: ${cd.average_percentage}%"></div>
                            </div>
                            <span class="text-xs font-bold text-slate-700 w-12">${cd.average_percentage}%</span>
                            <span class="text-xs px-2.5 py-1 rounded-full font-semibold ${cd.difficulty_rating === 'Challenging' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}">
                                ${cd.difficulty_rating}
                            </span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

