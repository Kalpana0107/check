// Student Dashboard Management Logic

let currentStudentSubmissions = [];
let activeReportCard = null;
let trendChartInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Auth check
    const user = App.getUser();
    if (!user || user.role !== 'student') {
        App.showToast('Please sign in as a student', 'error');
        setTimeout(() => window.location.href = '/', 1000);
        return;
    }

    document.getElementById('student-name').textContent = user.full_name;
    document.getElementById('student-email').textContent = user.email;

    await loadStudentOverview();
    await loadActiveExamsDropdown();
    await loadStudentSubmissions();
    initStudentDropZone();
});

function switchStudentTab(tabName) {
    const tabs = ['reports', 'upload', 'growth'];
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

    if (tabName === 'growth') {
        loadGrowthAnalyticsTab();
    }
}

async function loadStudentOverview() {
    try {
        const analytics = await App.apiFetch('/api/analytics/student');
        document.getElementById('stat-total-exams').textContent = analytics.total_exams_taken;
        document.getElementById('stat-avg-score').textContent = `${analytics.average_score_pct}%`;
        document.getElementById('stat-top-chapter').textContent = analytics.top_strengths[0] || 'Thermodynamics';
        document.getElementById('stat-weak-count').textContent = analytics.weak_areas.length;
    } catch (err) {
        console.error('Error loading analytics overview:', err);
    }
}

async function loadActiveExamsDropdown() {
    const select = document.getElementById('select-exam');
    if (!select) return;

    try {
        const exams = await App.apiFetch('/api/exams/all-active');
        select.innerHTML = exams.map(e => `
            <option value="${e.id}">${e.subject}: ${e.title} (${e.total_marks} Marks)</option>
        `).join('');
    } catch (err) {
        select.innerHTML = `<option value="">Failed to load exams</option>`;
    }
}

async function loadStudentSubmissions() {
    const container = document.getElementById('submissions-list-container');
    if (!container) return;

    container.innerHTML = `<div class="p-8 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Loading your evaluated exams...</div>`;

    try {
        const subs = await App.apiFetch('/api/submissions/my');
        currentStudentSubmissions = subs;

        if (subs.length === 0) {
            container.innerHTML = `
                <div class="bg-white rounded-xl p-8 text-center border border-slate-200">
                    <i class="fa-solid fa-file-circle-check text-4xl text-slate-300 mb-3"></i>
                    <h4 class="font-bold text-slate-700 mb-1">No Evaluated Exams Yet</h4>
                    <p class="text-xs text-slate-500 mb-4">Upload an answer paper in the "Upload Answer Sheet" tab to get instant multimodal conceptual evaluation.</p>
                    <button onclick="switchStudentTab('upload')" class="bg-blue-600 hover:bg-blue-700 text-white text-xs px-5 py-2.5 rounded-full font-semibold transition">
                        Upload Paper Now
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = subs.map(s => {
            const isReady = s.status === 'published' || s.status === 'graded';
            const dateStr = new Date(s.submitted_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
            
            return `
                <div class="bg-white rounded-xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition">
                    <div class="flex flex-wrap items-start justify-between gap-4 mb-4">
                        <div>
                            <span class="inline-block bg-blue-100 text-blue-700 text-xs px-2.5 py-0.5 rounded-full font-bold mb-2">${s.subject}</span>
                            <h3 class="text-lg font-bold text-slate-900">${s.exam_title}</h3>
                            <p class="text-xs text-slate-400 mt-1">Submitted on ${dateStr} &bull; Paper: ${s.file_name}</p>
                        </div>
                        <div class="text-right">
                            ${isReady ? `
                                <div class="text-3xl font-black text-blue-600">${s.total_score}<span class="text-base text-slate-400">/${s.max_score}</span></div>
                                <div class="inline-block bg-emerald-100 text-emerald-800 text-xs px-2.5 py-0.5 rounded-full font-bold mt-1">${s.percentage}% &bull; Evaluated</div>
                            ` : `
                                <div class="text-xs bg-amber-100 text-amber-800 px-3 py-1 rounded-full font-semibold">Evaluation in Progress</div>
                            `}
                        </div>
                    </div>

                    ${s.teacher_notes ? `
                        <div class="bg-slate-50 p-3 rounded-lg border border-slate-100 text-xs text-slate-600 mb-4 flex items-start gap-2">
                            <i class="fa-solid fa-comment-dots text-blue-500 mt-0.5"></i>
                            <div><strong>Teacher / AI Feedback:</strong> ${s.teacher_notes}</div>
                        </div>
                    ` : ''}

                    <div class="flex justify-between items-center pt-3 border-t border-slate-100">
                        <span class="text-xs text-slate-500"><i class="fa-solid fa-microchip text-blue-500 mr-1"></i>Multimodal Conceptual OCR</span>
                        <button onclick="viewReportCard(${s.id})" class="bg-blue-600 hover:bg-blue-700 text-white text-xs px-4 py-2 rounded-lg font-semibold transition shadow-sm flex items-center gap-2">
                            <i class="fa-solid fa-file-invoice"></i> View Detailed Report Card
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // If there's at least one submission, load report card modal automatically if none loaded
        if (subs.length > 0 && !activeReportCard) {
            // viewReportCard(subs[0].id);
        }

    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-red-500">Failed to load submissions: ${err.message}</div>`;
    }
}

async function viewReportCard(submissionId) {
    const modal = document.getElementById('report-modal');
    modal.classList.remove('hidden');

    const content = document.getElementById('report-modal-content');
    content.innerHTML = `<div class="text-center py-16 text-slate-400"><i class="fa-solid fa-spinner fa-spin text-3xl mb-3 text-blue-600"></i><p>Loading your evaluated report card...</p></div>`;

    try {
        const sub = await App.apiFetch(`/api/submissions/${submissionId}`);
        activeReportCard = sub;
        renderReportCard(sub);
    } catch (err) {
        content.innerHTML = `<div class="p-8 text-center text-red-600">Failed to load report card: ${err.message}</div>`;
    }
}

function closeReportModal() {
    const modal = document.getElementById('report-modal');
    modal.classList.add('hidden');
    activeReportCard = null;
}

function renderReportCard(sub) {
    const content = document.getElementById('report-modal-content');

    const questionsHtml = sub.evaluations.map(ev => {
        const isFull = ev.marks_awarded >= ev.max_marks;
        const isGood = ev.marks_awarded >= ev.max_marks * 0.7;

        return `
            <div class="bg-white rounded-xl p-5 border border-slate-200 shadow-sm mb-4">
                <div class="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2 border-b border-slate-100">
                    <div class="flex items-center gap-2">
                        <span class="w-7 h-7 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center">Q${ev.question_number}</span>
                        <span class="text-xs bg-blue-100 text-blue-800 font-semibold px-2.5 py-0.5 rounded-full">${ev.chapter_tag}</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-slate-500 font-medium">Marks Awarded:</span>
                        <span class="text-sm font-black ${isFull ? 'text-emerald-600' : (isGood ? 'text-blue-600' : 'text-amber-600')}">
                            ${ev.marks_awarded} / ${ev.max_marks}
                        </span>
                    </div>
                </div>

                ${ev.question_text ? `
                    <div class="mb-3 text-xs bg-slate-50 p-3 rounded-lg border border-slate-100 text-slate-800">
                        <span class="font-bold">Question:</span> ${ev.question_text}
                    </div>
                ` : ''}

                <div class="grid md:grid-cols-2 gap-4 mb-3 text-xs">
                    <div class="bg-slate-50 p-3 rounded-lg border border-slate-200">
                        <span class="font-bold text-slate-700 flex items-center gap-1 mb-1">
                            <i class="fa-solid fa-pen-nib text-slate-500"></i> Your Answer (Transcribed):
                        </span>
                        <p class="text-slate-600 leading-relaxed italic">${ev.student_extracted_text || 'Text extracted from paper'}</p>
                    </div>
                    <div class="bg-blue-50/50 p-3 rounded-lg border border-blue-100">
                        <span class="font-bold text-blue-900 flex items-center gap-1 mb-1">
                            <i class="fa-solid fa-key text-blue-500"></i> Model Answer Logic:
                        </span>
                        <p class="text-slate-700 leading-relaxed">${ev.model_answer || 'Expected physical reasoning'}</p>
                    </div>
                </div>

                <!-- Conceptual feedback -->
                <div class="bg-emerald-50/60 rounded-lg p-3 text-xs border border-emerald-100 mb-2">
                    <div class="font-bold text-emerald-900 mb-1 flex items-center gap-1">
                        <i class="fa-solid fa-circle-check text-emerald-600"></i> Conceptual Logic Breakdown:
                    </div>
                    <p class="text-emerald-800 leading-relaxed">${ev.conceptual_feedback}</p>
                </div>

                ${ev.improvement_tip ? `
                    <div class="bg-amber-50 rounded-lg p-3 text-xs border border-amber-200 flex items-start gap-2">
                        <i class="fa-solid fa-lightbulb text-amber-600 mt-0.5"></i>
                        <div class="text-amber-900">
                            <strong>Scope of Improvement:</strong> ${ev.improvement_tip}
                        </div>
                    </div>
                ` : ''}

                ${ev.teacher_comment ? `
                    <div class="mt-2 text-xs bg-purple-50 p-2.5 rounded-lg border border-purple-200 text-purple-900">
                        <strong>Teacher's Personal Note:</strong> ${ev.teacher_comment}
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');

    content.innerHTML = `
        <div class="space-y-6">
            <!-- Header Scorecard Banner -->
            <div class="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-6 text-white shadow-lg">
                <div class="flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <span class="inline-block bg-white/20 text-white text-xs px-2.5 py-0.5 rounded-full font-bold mb-2">${sub.subject}</span>
                        <h2 class="text-2xl font-black">${sub.exam_title}</h2>
                        <p class="text-blue-100 text-xs mt-1">Evaluated by Multimodal AI & Verified by Instructor</p>
                    </div>
                    <div class="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20 text-center min-w-[140px]">
                        <div class="text-xs uppercase font-bold text-blue-100 tracking-wider">Final Score</div>
                        <div class="text-4xl font-black mt-1">${sub.total_score}<span class="text-xl text-blue-200">/${sub.max_score}</span></div>
                        <div class="text-xs font-semibold bg-emerald-400 text-slate-900 px-2 py-0.5 rounded-full mt-2 inline-block">
                            ${sub.percentage}% Score
                        </div>
                    </div>
                </div>
            </div>

            <!-- Uploaded Answer Paper preview link -->
            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                <span class="text-slate-600"><i class="fa-solid fa-file-lines mr-1 text-blue-600"></i><strong>Original Paper:</strong> ${sub.file_name}</span>
                <a href="${sub.file_path}" target="_blank" class="text-blue-600 hover:underline font-semibold flex items-center gap-1">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> View Uploaded Image/PDF
                </a>
            </div>

            <!-- Question Breakdown -->
            <div>
                <h3 class="font-bold text-slate-900 text-base mb-3 flex items-center gap-2">
                    <i class="fa-solid fa-clipboard-check text-blue-600"></i> Question-by-Question Conceptual Evaluation
                </h3>
                ${questionsHtml}
            </div>

            <div class="flex justify-end pt-4 border-t border-slate-100">
                <button onclick="closeReportModal()" class="px-6 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition">
                    Close Report
                </button>
            </div>
        </div>
    `;
}

// Student upload paper logic
function initStudentDropZone() {
    const fileInput = document.getElementById('student-upload-file');
    if (!fileInput) return;

    fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files[0]) {
            const nameEl = document.getElementById('student-file-selected-name');
            nameEl.textContent = 'Selected: ' + fileInput.files[0].name;
            nameEl.classList.remove('hidden');
            fileInput.parentElement.classList.add('border-blue-500', 'bg-blue-50');
            fileInput.parentElement.classList.remove('border-slate-300');
        }
    });
}

async function handleStudentUploadSubmit(event) {
    event.preventDefault();
    const examId = document.getElementById('select-exam').value;
    const fileInput = document.getElementById('student-upload-file');

    if (!examId) {
        App.showToast('Please select an exam', 'error');
        return;
    }
    if (!fileInput.files || fileInput.files.length === 0) {
        App.showToast('Please choose your answer paper (image or PDF)', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('exam_id', examId);
    formData.append('file', fileInput.files[0]);
    formData.append('auto_evaluate', 'true');

    // UI state
    document.getElementById('upload-form-container').classList.add('hidden');
    const loadingContainer = document.getElementById('upload-loading-container');
    loadingContainer.classList.remove('hidden');
    loadingContainer.classList.add('flex');

    let progress = 0;
    const bar = document.getElementById('upload-progress-bar');
    const interval = setInterval(() => {
        progress += Math.floor(Math.random() * 20) + 10;
        if (progress >= 90) {
            progress = 90;
            clearInterval(interval);
        }
        bar.style.width = progress + '%';
    }, 300);

    try {
        const result = await App.apiFetch('/api/submissions/upload', {
            method: 'POST',
            body: formData
        });

        clearInterval(interval);
        bar.style.width = '100%';

        setTimeout(async () => {
            loadingContainer.classList.remove('flex');
            loadingContainer.classList.add('hidden');
            document.getElementById('upload-form-container').classList.remove('hidden');

            // Reset file input
            fileInput.value = '';
            document.getElementById('student-file-selected-name').classList.add('hidden');
            fileInput.parentElement.classList.remove('border-blue-500', 'bg-blue-50');
            fileInput.parentElement.classList.add('border-slate-300');
            bar.style.width = '0%';

            App.showToast('Paper uploaded and graded with Multimodal AI!', 'success');
            await loadStudentSubmissions();
            await loadStudentOverview();
            switchStudentTab('reports');
            viewReportCard(result.id);
        }, 600);

    } catch (err) {
        clearInterval(interval);
        loadingContainer.classList.remove('flex');
        loadingContainer.classList.add('hidden');
        document.getElementById('upload-form-container').classList.remove('hidden');
        App.showToast(`Upload failed: ${err.message}`, 'error');
    }
}

// Growth & Analytics Tab
async function loadGrowthAnalyticsTab() {
    try {
        const analytics = await App.apiFetch('/api/analytics/student');
        renderScoreTrendsChart(analytics.score_trends);
        renderImprovementScopeTable(analytics.chapter_breakdowns);
        renderPersonalizedRecommendations(analytics);
    } catch (err) {
        console.error('Error loading growth analytics:', err);
    }
}

function renderScoreTrendsChart(trends) {
    const ctx = document.getElementById('score-trends-chart');
    if (!ctx) return;

    if (trendChartInstance) {
        trendChartInstance.destroy();
    }

    if (!trends || trends.length === 0) {
        return;
    }

    const labels = trends.map(t => `${t.subject} (${t.date})`);
    const dataPoints = trends.map(t => t.percentage);

    trendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Exam Score Percentage (%)',
                data: dataPoints,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.08)',
                borderWidth: 3,
                pointBackgroundColor: '#1d4ed8',
                pointRadius: 6,
                pointHoverRadius: 8,
                fill: true,
                tension: 0.35
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: val => val + '%'
                    },
                    grid: {
                        color: '#f1f5f9'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: ctx => `Score: ${ctx.parsed.y}%`
                    }
                }
            }
        }
    });
}

function renderImprovementScopeTable(chapters) {
    const tableBody = document.getElementById('improvement-table-body');
    if (!tableBody) return;

    if (!chapters || chapters.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-slate-400">No chapter performance data yet.</td></tr>`;
        return;
    }

    tableBody.innerHTML = chapters.map(c => {
        const badgeClasses = {
            'High Priority': 'bg-amber-100 text-amber-800',
            'Medium Priority': 'bg-blue-100 text-blue-800',
            'Mastered': 'bg-emerald-100 text-emerald-800'
        };

        return `
            <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                <td class="px-6 py-4">
                    <div class="font-bold text-slate-900">${c.chapter_tag}</div>
                    <div class="text-xs text-slate-400">${c.subject}</div>
                </td>
                <td class="px-6 py-4">
                    <span class="font-bold text-slate-800">${c.total_marks_earned}</span> <span class="text-xs text-slate-400">/ ${c.total_marks_possible}</span>
                </td>
                <td class="px-6 py-4 font-bold text-slate-800">${c.percentage}%</td>
                <td class="px-6 py-4 font-extrabold text-amber-600">-${c.improvement_scope}</td>
                <td class="px-6 py-4">
                    <span class="text-xs px-2.5 py-1 rounded-full font-bold ${badgeClasses[c.priority_level] || 'bg-slate-100 text-slate-700'}">
                        ${c.priority_level}
                    </span>
                </td>
                <td class="px-6 py-4 text-xs text-slate-600 max-w-xs">${c.recommended_action}</td>
            </tr>
        `;
    }).join('');
}

function renderPersonalizedRecommendations(data) {
    const container = document.getElementById('personalized-tips-container');
    if (!container) return;

    container.innerHTML = `
        <div class="grid md:grid-cols-2 gap-4">
            <div class="bg-blue-50/70 p-5 rounded-xl border border-blue-100">
                <h4 class="font-bold text-blue-900 text-sm mb-2 flex items-center gap-2">
                    <i class="fa-solid fa-award text-blue-600"></i> Top Conceptual Strengths
                </h4>
                <div class="flex flex-wrap gap-2">
                    ${data.top_strengths.map(s => `
                        <span class="bg-white text-blue-700 text-xs px-3 py-1.5 rounded-lg border border-blue-200 font-semibold shadow-sm">
                            <i class="fa-solid fa-check text-emerald-500 mr-1"></i>${s}
                        </span>
                    `).join('') || '<span class="text-xs text-slate-500">Keep completing exams to unlock strength badges</span>'}
                </div>
            </div>

            <div class="bg-amber-50/70 p-5 rounded-xl border border-amber-100">
                <h4 class="font-bold text-amber-900 text-sm mb-2 flex items-center gap-2">
                    <i class="fa-solid fa-bullseye text-amber-600"></i> Recommended Focus Chapters
                </h4>
                <ul class="text-xs text-amber-900 space-y-2">
                    ${data.personalized_tips.map(tip => `
                        <li class="flex items-start gap-2">
                            <i class="fa-solid fa-arrow-right text-amber-500 mt-0.5"></i>
                            <span>${tip}</span>
                        </li>
                    `).join('')}
                </ul>
            </div>
        </div>
    `;
}

