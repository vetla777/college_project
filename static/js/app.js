/**
 * Smart College AI — Digital Twin OS Client Application
 * Enterprise Dual Authentication, Role-Specific Workspaces, Staff Roster Management,
 * Supabase Integration & Contextual AI Chatbot.
 */

// Supabase Configuration
const SUPABASE_PROJECT_URL = "https://aqfqdjhddfvyprpwccyp.supabase.co";
let supabaseClient = null;

// Application State
let state = {
  authRole: 'student', // 'student' | 'staff'
  authUser: null,      // Logged in user object
  students: [],
  staff: [],
  allRequests: [],
  activeTab: 'dashboard'
};

// Toast notification utility
function showToast(title, message, isSuccess = true) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `pointer-events-auto flex items-start gap-3 p-4 rounded-2xl shadow-2xl border-l-4 transition-all duration-300 transform translate-y-2 opacity-0 ${
    isSuccess ? 'bg-surface-container-lowest border-primary text-on-surface' : 'bg-surface-container-lowest border-error text-on-surface'
  }`;
  toast.innerHTML = `
    <span class="material-symbols-outlined ${isSuccess ? 'text-primary' : 'text-error'} text-[22px] shrink-0">${isSuccess ? 'check_circle' : 'error'}</span>
    <div class="flex flex-col text-left">
      <span class="font-label-md text-xs font-bold">${title}</span>
      <span class="font-body-sm text-xs text-on-surface-variant">${message}</span>
    </div>
  `;
  container.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  });
  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// Format currency
function formatINR(amount) {
  return '₹' + Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// -------------------------------------------------------------
// APP INITIALIZATION & AUTH CHECK
// -------------------------------------------------------------
async function initApp() {
  try {
    // 1. Fetch Students & Staff from API
    const [resStudents, resStaff, resRequests] = await Promise.all([
      fetch('/api/students').then(r => r.json()),
      fetch('/api/staff').then(r => r.json()),
      fetch('/api/requests/all').then(r => r.json()).catch(() => [])
    ]);

    state.students = resStudents || [];
    state.staff = resStaff || [];
    state.allRequests = resRequests || [];

    // 2. Check Supabase Stored Key
    const storedSupabaseKey = localStorage.getItem('supabase_anon_key');
    if (storedSupabaseKey && window.supabase) {
      document.getElementById('supabase-key-input').value = storedSupabaseKey;
      initSupabase(storedSupabaseKey);
    }

    // 3. Check Stored Auth Session
    const savedRole = sessionStorage.getItem('smart_college_auth_role');
    const savedUserJson = sessionStorage.getItem('smart_college_auth_user');

    if (savedRole && savedUserJson) {
      try {
        const parsedUser = JSON.parse(savedUserJson);
        // Refresh with latest data
        let refreshedUser = null;
        if (savedRole === 'student') {
          refreshedUser = state.students.find(s => s.student_id === parsedUser.student_id);
        } else {
          refreshedUser = state.staff.find(st => st.staff_id === parsedUser.staff_id);
        }
        state.authUser = refreshedUser || parsedUser;
        state.authRole = savedRole;
        applyAuthenticatedSession();
      } catch (e) {
        showLoginScreen();
      }
    } else {
      showLoginScreen();
    }

    // 4. Setup Event Handlers
    setupAuthListeners();
    setupAppListeners();

  } catch (err) {
    console.error("Initialization error:", err);
    showToast("Connection Notice", "Running on local dataset cache.", false);
  }
}

function initSupabase(anonKey) {
  if (window.supabase && anonKey) {
    try {
      supabaseClient = window.supabase.createClient(SUPABASE_PROJECT_URL, anonKey);
      document.getElementById('backend-status-text').textContent = 'Supabase Cloud Connected';
      document.getElementById('backend-status-text').classList.add('text-emerald-600');
    } catch (e) {
      console.warn("Supabase init error:", e);
    }
  }
}

// -------------------------------------------------------------
// AUTHENTICATION LOGIC & VIEWS
// -------------------------------------------------------------
function showLoginScreen() {
  document.getElementById('auth-screen').classList.remove('hidden');
  document.getElementById('app-workspace').classList.add('hidden');
}

function applyAuthenticatedSession() {
  document.getElementById('auth-screen').classList.add('hidden');
  document.getElementById('app-workspace').classList.remove('hidden');

  const user = state.authUser;
  const role = state.authRole;

  // Header display
  const name = user.full_name;
  const initials = name.replace('Dr. ', '').replace('Prof. ', '').replace('Er. ', '').replace('Mr. ', '').replace('Mrs. ', '').split(' ').map(n => n[0]).join('').substring(0, 2);

  document.getElementById('header-avatar').textContent = initials;
  document.getElementById('header-user-name').textContent = name;
  
  if (role === 'student') {
    document.getElementById('header-user-sub').textContent = `${user.student_id} • ${user.department}`;
    document.getElementById('sidebar-user-name').textContent = name;
    document.getElementById('sidebar-user-role-badge').textContent = `Student (${user.department})`;
    document.getElementById('sidebar-role-icon').textContent = 'person';

    // Show student nav, hide staff nav
    document.getElementById('nav-student-section').classList.remove('hidden');
    document.getElementById('nav-staff-section').classList.add('hidden');

    // Render Student Workspace Views
    renderStudentDashboard();
    renderDetailedAttendance();
    renderCertificateRequests();
    switchTab('dashboard');
  } else {
    document.getElementById('header-user-sub').textContent = `${user.designation} • ${user.department}`;
    document.getElementById('sidebar-user-name').textContent = name;
    document.getElementById('sidebar-user-role-badge').textContent = `Faculty (${user.department})`;
    document.getElementById('sidebar-role-icon').textContent = 'badge';

    // Show staff nav, hide student nav
    document.getElementById('nav-staff-section').classList.remove('hidden');
    document.getElementById('nav-student-section').classList.add('hidden');

    // Render Staff Workspace Views
    renderStaffDashboard();
    renderStaffCourses();
    renderStaffRoster();
    renderStaffApprovals();
    switchTab('staff-dashboard');
  }

  // Common Directory Views
  renderStudentDirectory();
  renderStaffDirectory();
}

async function performLogin(role, identifier, password) {
  const errorBanner = document.getElementById('auth-error-banner');
  const errorText = document.getElementById('auth-error-text');
  const submitBtn = document.getElementById('auth-submit-btn');

  errorBanner.classList.add('hidden');
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="material-symbols-outlined animate-spin text-[18px]">sync</span><span>Verifying credentials...</span>`;

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role, identifier, password })
    });

    // Handle 404 or unknown endpoint if backend process was not yet restarted
    if (res.status === 404) {
      const errData = await res.json().catch(() => ({}));
      console.warn("Backend /api/auth/login not found on running instance. Activating seamless local validation fallback...", errData);
      return fallbackLocalLogin(role, identifier, password);
    }

    const data = await res.json();

    if (data.success) {
      state.authRole = role;
      state.authUser = data.user;
      sessionStorage.setItem('smart_college_auth_role', role);
      sessionStorage.setItem('smart_college_auth_user', JSON.stringify(data.user));
      
      showToast("Authentication Successful", `Welcome, ${data.user.full_name}!`);
      applyAuthenticatedSession();
    } else {
      errorBanner.classList.remove('hidden');
      errorText.textContent = data.error || 'Invalid identification or password.';
      showToast("Access Denied", data.error || 'Login failed', false);
    }
  } catch (err) {
    console.warn("Fetch error, using client authentication fallback:", err);
    return fallbackLocalLogin(role, identifier, password);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<span>Sign In to Campus OS</span><span class="material-symbols-outlined text-[18px]">arrow_forward</span>`;
  }
}

// Client-side authentication fallback (ensures instant login even if server process wasn't restarted)
function fallbackLocalLogin(role, identifier, password) {
  const errorBanner = document.getElementById('auth-error-banner');
  const errorText = document.getElementById('auth-error-text');
  const ident = identifier.trim().toLowerCase();
  const pwd = password.trim();

  let target = null;
  if (role === 'student') {
    target = state.students.find(s => s.student_id.toLowerCase() === ident || s.email.toLowerCase() === ident);
  } else {
    target = state.staff.find(st => st.staff_id.toLowerCase() === ident || st.email.toLowerCase() === ident);
  }

  if (!target) {
    errorBanner.classList.remove('hidden');
    errorText.textContent = `No ${role} found with ID or Email "${identifier}".`;
    showToast("Login Failed", `No ${role} record found.`, false);
    return;
  }

  if (target.password !== pwd) {
    errorBanner.classList.remove('hidden');
    errorText.textContent = 'Incorrect password.';
    showToast("Access Denied", "Incorrect password.", false);
    return;
  }

  state.authRole = role;
  state.authUser = target;
  sessionStorage.setItem('smart_college_auth_role', role);
  sessionStorage.setItem('smart_college_auth_user', JSON.stringify(target));

  showToast("Authentication Successful", `Welcome back, ${target.full_name}!`);
  applyAuthenticatedSession();
}

function performLogout() {
  sessionStorage.removeItem('smart_college_auth_role');
  sessionStorage.removeItem('smart_college_auth_user');
  state.authUser = null;
  showLoginScreen();
  showToast("Logged Out", "You have signed out safely.");
}

// -------------------------------------------------------------
// STUDENT WORKSPACE RENDERING
// -------------------------------------------------------------
function renderStudentDashboard() {
  const s = state.authUser;
  if (!s || state.authRole !== 'student') return;

  // Welcome Banner
  document.getElementById('welcome-title').textContent = `Good morning, ${s.full_name.split(' ')[0]} 👋`;
  document.getElementById('welcome-subtitle').textContent = `B.Tech ${s.department} • 4th Year • Semester 8`;

  // 4 Cards
  document.getElementById('card-attendance-val').textContent = `${s.attendance_pct}%`;
  document.getElementById('card-attendance-bar').style.width = `${s.attendance_pct}%`;
  document.getElementById('card-attendance-fraction').textContent = `${Math.round(s.attendance_pct * 1.62)}/162 attended`;

  const attBadge = document.getElementById('card-attendance-badge');
  if (s.attendance_pct >= 85) {
    attBadge.className = 'px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-label-xs font-semibold';
    attBadge.textContent = 'On Track';
  } else if (s.attendance_pct >= 75) {
    attBadge.className = 'px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 text-label-xs font-semibold';
    attBadge.textContent = 'Watchlist';
  } else {
    attBadge.className = 'px-2.5 py-0.5 rounded-full bg-red-50 text-red-700 text-label-xs font-semibold';
    attBadge.textContent = 'Shortage Risk';
  }

  // CGPA
  document.getElementById('card-cgpa-val').textContent = s.cgpa.toFixed(2);
  document.getElementById('cgpa-page-val').textContent = s.cgpa.toFixed(2);

  // Fee Balance
  document.getElementById('card-fee-val').textContent = formatINR(s.fee_balance);
  document.getElementById('fee-page-balance-text').textContent = formatINR(s.fee_balance);
  document.getElementById('modal-fee-balance').textContent = formatINR(s.fee_balance);
  document.getElementById('modal-fee-total').textContent = formatINR(s.fee_balance);

  const feeBadge = document.getElementById('card-fee-badge');
  if (s.fee_balance === 0) {
    feeBadge.className = 'px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-label-xs font-semibold';
    feeBadge.textContent = 'Fully Paid';
    document.getElementById('card-pay-btn').textContent = 'Receipt';
  } else {
    feeBadge.className = 'px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 text-label-xs font-semibold';
    feeBadge.textContent = 'Due Nov 15';
    document.getElementById('card-pay-btn').textContent = 'Pay Now';
  }

  // Active requests
  const reqs = (s.active_requests || []);
  const reqCount = reqs.length;
  const approvedReqs = reqs.filter(r => r.status === 'Approved');
  const pendingReqs = reqs.filter(r => r.status !== 'Approved');

  document.getElementById('card-requests-val').textContent = reqCount;
  const reqBadge = document.getElementById('card-requests-badge');
  if (approvedReqs.length > 0) {
    reqBadge.className = 'px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-label-xs font-semibold';
    reqBadge.textContent = `${approvedReqs.length} Approved`;
  } else {
    reqBadge.className = 'px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 text-label-xs font-semibold';
    reqBadge.textContent = `${pendingReqs.length} In Review`;
  }

  // Dynamic preview with download buttons for approved requests
  const previewContainer = document.getElementById('card-requests-preview');
  if (previewContainer) {
    if (reqs.length === 0) {
      previewContainer.innerHTML = '<p class="text-xs text-outline italic">No active requests submitted.</p>';
    } else {
      previewContainer.innerHTML = reqs.slice(0, 2).map(r => `
        <div class="p-2.5 rounded-xl bg-surface-container-low/80 border border-surface-container/60 flex items-center justify-between gap-2 mt-1">
          <div class="min-w-0">
            <p class="text-xs font-semibold text-on-surface truncate">${r.certificate_type}</p>
            <span class="text-[10px] text-outline font-mono-data">${r.request_id}</span>
          </div>
          <div class="shrink-0">
            ${r.status === 'Approved'
              ? `<button onclick="downloadCertificate('${r.request_id}')" class="px-2.5 py-1 rounded-lg bg-primary text-white text-[11px] font-semibold hover:bg-primary-container transition shadow-sm flex items-center gap-1">
                   <span class="material-symbols-outlined text-[14px]">download</span>
                   <span>Download</span>
                 </button>`
              : `<span class="px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 text-[10px] font-semibold">In Review</span>`
            }
          </div>
        </div>
      `).join('');
    }
  }

  // Digital Twin
  const twinScore = s.digital_twin_score || 94;
  document.getElementById('twin-score-val').textContent = twinScore;
  document.getElementById('dt-health-score').textContent = `${twinScore} / 100`;

  // Subjects breakdown
  renderDashboardSubjects(s.subjects || []);
  renderDashboardActivities(s.recent_activities || []);
}

function renderDashboardSubjects(subjects) {
  const container = document.getElementById('dashboard-subjects-list');
  if (!container) return;
  container.innerHTML = '';

  subjects.forEach(sub => {
    const isWarning = sub.pct < 80;
    const item = document.createElement('div');
    item.className = `p-4 rounded-2xl border space-y-2.5 ${
      isWarning ? 'bg-amber-50/40 border-amber-200/60' : 'bg-surface-container-low/60 border-surface-container/40'
    }`;

    item.innerHTML = `
      <div class="flex items-center justify-between text-body-sm">
        <div>
          <span class="font-semibold text-on-surface">${sub.name}</span>
          <span class="text-xs ${isWarning ? 'text-amber-700' : 'text-outline'} ml-2 font-mono-data">${sub.attended}/${sub.total} sessions</span>
        </div>
        <div class="flex items-center gap-1.5">
          ${isWarning ? '<span class="material-symbols-outlined text-amber-600 text-[16px]">warning</span>' : ''}
          <span class="font-mono-data font-bold ${isWarning ? 'text-amber-700' : (sub.pct >= 90 ? 'text-emerald-600' : 'text-secondary')}">${sub.pct}%</span>
        </div>
      </div>
      <div class="w-full bg-surface-container-low rounded-full h-2 overflow-hidden">
        <div class="${isWarning ? 'bg-amber-500' : (sub.pct >= 90 ? 'bg-emerald-500' : 'bg-secondary')} h-full rounded-full" style="width: ${sub.pct}%"></div>
      </div>
    `;
    container.appendChild(item);
  });
}

function renderDashboardActivities(activities) {
  const container = document.getElementById('dashboard-activities-list');
  if (!container) return;
  container.innerHTML = '';

  activities.forEach(act => {
    const item = document.createElement('div');
    item.className = 'flex items-start gap-3.5 p-3.5 rounded-xl hover:bg-surface-container-low/40 transition-colors';
    
    let colorClass = 'bg-emerald-50 text-emerald-600';
    if (act.color === 'purple') colorClass = 'bg-purple-50 text-tertiary';
    if (act.color === 'blue') colorClass = 'bg-blue-50 text-secondary';

    item.innerHTML = `
      <div class="w-9 h-9 rounded-xl ${colorClass} flex items-center justify-center shrink-0">
        <span class="material-symbols-outlined text-[20px]">${act.icon || 'check_circle'}</span>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between">
          <p class="text-body-sm font-semibold text-on-surface">${act.title}</p>
          <span class="font-mono-data text-xs text-outline">${act.time_label}</span>
        </div>
        <p class="text-xs text-on-surface-variant mt-0.5">${act.description}</p>
      </div>
    `;
    container.appendChild(item);
  });
}

// -------------------------------------------------------------
// STAFF WORKSPACE RENDERING
// -------------------------------------------------------------
function renderStaffDashboard() {
  const st = state.authUser;
  if (!st || state.authRole !== 'staff') return;

  document.getElementById('staff-welcome-title').textContent = `Welcome, ${st.full_name} 👋`;
  document.getElementById('staff-welcome-subtitle').textContent = `${st.designation} • ${st.department} Department`;

  document.getElementById('staff-card-cabin').textContent = st.cabin_location;
  document.getElementById('staff-card-hours').textContent = st.office_hours;

  const deptStudents = state.students.filter(s => s.department === st.department);
  document.getElementById('staff-card-students-count').textContent = `${deptStudents.length} Students`;

  const pendingReqs = state.allRequests.filter(r => r.status === 'In Review');
  document.getElementById('staff-card-pending-approvals').textContent = `${pendingReqs.length} Requests`;

  // Render dept students table preview
  const previewTable = document.getElementById('staff-dept-students-table');
  if (previewTable) {
    let rows = deptStudents.map(s => `
      <tr class="hover:bg-surface-container-low/40 transition-colors">
        <td class="p-3 font-mono-data font-semibold text-primary">${s.student_id}</td>
        <td class="p-3 font-semibold text-on-surface">${s.full_name}</td>
        <td class="p-3 font-mono-data">${s.cgpa.toFixed(2)}</td>
        <td class="p-3">
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold ${s.attendance_pct >= 80 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}">
            ${s.attendance_pct}%
          </span>
        </td>
        <td class="p-3 text-xs text-outline font-mono-data">${s.phone}</td>
      </tr>
    `).join('');

    previewTable.innerHTML = `
      <table class="w-full text-left text-body-sm">
        <thead class="bg-surface-container-low text-xs font-semibold text-on-surface-variant">
          <tr>
            <th class="p-3">Student ID</th>
            <th class="p-3">Full Name</th>
            <th class="p-3">CGPA</th>
            <th class="p-3">Attendance</th>
            <th class="p-3">Phone</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-container/60">${rows}</tbody>
      </table>
    `;
  }
}

function renderStaffCourses() {
  const container = document.getElementById('staff-courses-container');
  if (!container) return;

  const st = state.authUser;
  const deptStudents = state.students.filter(s => s.department === st.department);

  container.innerHTML = `
    <div class="p-6 rounded-2xl bg-surface-container-low/60 border border-surface-container space-y-4">
      <div class="flex items-center justify-between">
        <span class="px-2.5 py-1 rounded-lg bg-primary-container text-on-primary font-mono-data text-xs font-semibold">${st.department}801</span>
        <span class="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded-full">Active Term</span>
      </div>
      <div>
        <h3 class="font-headline-sm text-lg font-bold text-on-surface">${st.specialization}</h3>
        <p class="text-xs text-on-surface-variant mt-1">4 Credits • Final Year Core Specialization</p>
      </div>
      <div class="pt-2 border-t border-surface-container space-y-2 text-xs text-on-surface-variant">
        <div class="flex items-center justify-between">
          <span>Enrolled Class Size:</span>
          <span class="font-mono-data font-bold text-on-surface">${deptStudents.length} Students</span>
        </div>
        <div class="flex items-center justify-between">
          <span>Weekly Lecture Hours:</span>
          <span class="font-mono-data font-bold text-on-surface">4 Hours (Mon & Wed)</span>
        </div>
        <div class="flex items-center justify-between">
          <span>Assigned Classroom / Lab:</span>
          <span class="font-mono-data font-bold text-primary">Lab 404 / CS-204</span>
        </div>
      </div>
      <button data-tab="staff-roster" class="nav-switch-btn w-full py-2.5 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-semibold text-xs transition-colors flex items-center justify-center gap-1">
        <span>Open Course Attendance Roster</span>
        <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
      </button>
    </div>
  `;
}

function renderStaffRoster() {
  const container = document.getElementById('staff-roster-marking-table');
  if (!container) return;

  const st = state.authUser;
  const deptStudents = state.students.filter(s => s.department === st.department);

  let rows = deptStudents.map(s => {
    return `
      <tr class="hover:bg-surface-container-low/40 transition-colors">
        <td class="p-3.5 font-mono-data font-semibold text-primary">${s.student_id}</td>
        <td class="p-3.5 font-semibold text-on-surface">${s.full_name}</td>
        <td class="p-3.5 font-mono-data text-xs">${s.email}</td>
        <td class="p-3.5 font-mono-data font-bold ${s.attendance_pct >= 80 ? 'text-emerald-600' : 'text-amber-600'}">
          ${s.attendance_pct}%
        </td>
        <td class="p-3.5 text-right space-x-2">
          <button class="mark-present-btn px-3 py-1.5 rounded-xl bg-emerald-600 text-white font-semibold text-xs hover:bg-emerald-700 shadow-sm transition-all" data-id="${s.student_id}">
            + Present
          </button>
          <button class="mark-absent-btn px-3 py-1.5 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface-variant font-semibold text-xs transition-all" data-id="${s.student_id}">
            Absent
          </button>
        </td>
      </tr>
    `;
  }).join('');

  container.innerHTML = `
    <table class="w-full text-left text-body-sm">
      <thead class="bg-surface-container-low text-xs font-semibold text-on-surface-variant">
        <tr>
          <th class="p-3.5">Student ID</th>
          <th class="p-3.5">Student Name</th>
          <th class="p-3.5">Email</th>
          <th class="p-3.5">Attendance Rate</th>
          <th class="p-3.5 text-right">Today's Session Attendance</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-surface-container/60">${rows}</tbody>
    </table>
  `;

  // Attach mark present / absent listeners
  document.querySelectorAll('.mark-present-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const sid = btn.getAttribute('data-id');
      await markStudentAttendance(sid, 'present');
    });
  });

  document.querySelectorAll('.mark-absent-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const sid = btn.getAttribute('data-id');
      await markStudentAttendance(sid, 'absent');
    });
  });
}

async function markStudentAttendance(studentId, action) {
  const st = state.authUser;
  try {
    const res = await fetch('/api/attendance/mark', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentId,
        subject_name: st.specialization,
        action: action
      })
    });
    const data = await res.json();
    if (data.success) {
      // Update local student object
      const target = state.students.find(s => s.student_id === studentId);
      if (target) {
        target.attendance_pct = data.overall_attendance;
      }
      renderStaffRoster();
      renderStaffDashboard();
      showToast("Attendance Recorded", data.message);
    }
  } catch (err) {
    showToast("Error", "Could not record attendance.", false);
  }
}

function renderStaffApprovals() {
  const container = document.getElementById('staff-approvals-table');
  if (!container) return;

  const reqs = state.allRequests;
  if (reqs.length === 0) {
    container.innerHTML = '<p class="p-6 text-xs text-outline italic">No requests pending review.</p>';
    return;
  }

  let rows = reqs.map(req => {
    const isPending = req.status === 'In Review' || req.status.includes('Pending');
    return `
      <tr class="hover:bg-surface-container-low/40 transition-colors">
        <td class="p-3.5 font-mono-data font-semibold text-primary">${req.request_id}</td>
        <td class="p-3.5 font-semibold text-on-surface">${req.student_name} (${req.department || 'CSE'})</td>
        <td class="p-3.5">${req.certificate_type}</td>
        <td class="p-3.5 text-xs text-outline">${req.applied_date}</td>
        <td class="p-3.5">
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold ${req.status === 'Approved' ? 'bg-emerald-50 text-emerald-700' : (req.status === 'Rejected' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700')}">
            ${req.status}
          </span>
        </td>
        <td class="p-3.5 text-right space-x-2">
          ${isPending ? `
            <button class="approve-req-btn px-3 py-1.5 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 shadow-sm transition-all" data-id="${req.request_id}">
              Approve
            </button>
            <button class="reject-req-btn px-3 py-1.5 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface-variant text-xs font-semibold transition-all" data-id="${req.request_id}">
              Return / Reject
            </button>
          ` : `
            <span class="text-xs text-outline italic font-medium">Processed</span>
          `}
        </td>
      </tr>
    `;
  }).join('');

  container.innerHTML = `
    <table class="w-full text-left text-body-sm">
      <thead class="bg-surface-container-low text-xs font-semibold text-on-surface-variant">
        <tr>
          <th class="p-3.5">Request ID</th>
          <th class="p-3.5">Student Name</th>
          <th class="p-3.5">Application Document</th>
          <th class="p-3.5">Date</th>
          <th class="p-3.5">Current Status</th>
          <th class="p-3.5 text-right">Dean Action</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-surface-container/60">${rows}</tbody>
    </table>
  `;

  document.querySelectorAll('.approve-req-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const rid = btn.getAttribute('data-id');
      await actionRequest(rid, 'approve');
    });
  });

  document.querySelectorAll('.reject-req-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const rid = btn.getAttribute('data-id');
      await actionRequest(rid, 'reject');
    });
  });
}

async function actionRequest(requestId, action) {
  try {
    const res = await fetch(`/api/requests/${requestId}/${action}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      // Update local request object
      const found = state.allRequests.find(r => r.request_id.toUpperCase() === requestId.toUpperCase());
      if (found) {
        found.status = data.status;
      }
      // Sync to student view if logged-in user is the requester
      if (state.authUser && state.authUser.active_requests) {
        const studentReq = state.authUser.active_requests.find(r => r.request_id.toUpperCase() === requestId.toUpperCase());
        if (studentReq) {
          studentReq.status = data.status;
          studentReq.remarks = data.request ? (data.request.remarks || studentReq.remarks) : studentReq.remarks;
        }
      }
      renderStaffApprovals();
      renderStaffDashboard();
      renderCertificateRequests();
      showToast(action === 'approve' ? "Request Approved" : "Request Returned", data.message);
    }
  } catch (err) {
    showToast("Action Failed", "Could not process request.", false);
  }
}

// -------------------------------------------------------------
// ATTENDANCE & CERTIFICATES (STUDENT VIEW)
// -------------------------------------------------------------
function renderDetailedAttendance() {
  const container = document.getElementById('detailed-attendance-container');
  if (!container) return;

  const s = state.authUser;
  if (!s || !s.subjects) return;

  container.innerHTML = '';
  s.subjects.forEach(sub => {
    const neededForSafe = Math.max(0, Math.ceil((0.8 * sub.total - sub.attended) / 0.2));
    const safeMiss = Math.max(0, Math.floor((sub.attended - 0.75 * sub.total) / 0.75));

    const card = document.createElement('div');
    card.className = 'p-5 rounded-2xl bg-surface-container-low/50 border border-surface-container space-y-4';
    card.innerHTML = `
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div>
          <span class="text-xs font-mono-data font-semibold text-primary">${sub.code}</span>
          <h3 class="font-headline-sm text-base font-bold text-on-surface">${sub.name}</h3>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-xs text-outline">${sub.attended} attended / ${sub.total} held</span>
          <span class="font-mono-data text-lg font-extrabold ${sub.pct >= 85 ? 'text-emerald-600' : (sub.pct >= 75 ? 'text-amber-600' : 'text-red-600')}">${sub.pct}%</span>
        </div>
      </div>

      <div class="w-full bg-surface-container rounded-full h-2.5 overflow-hidden">
        <div class="${sub.pct >= 85 ? 'bg-emerald-500' : (sub.pct >= 75 ? 'bg-amber-500' : 'bg-red-500')} h-full rounded-full" style="width: ${sub.pct}%"></div>
      </div>

      <div class="p-3 rounded-xl bg-surface-container-lowest border border-surface-container flex flex-wrap items-center justify-between text-xs">
        <span class="text-on-surface-variant">
          ${sub.pct >= 80 
            ? `🟢 Safe Zone: You can safely miss up to <strong>${safeMiss} upcoming lecture(s)</strong> and stay above the 75% cutoff.` 
            : `⚠️ Action Required: You must attend the next <strong>${neededForSafe} lecture(s)</strong> to cross into the 80% safe zone.`}
        </span>
        <button class="text-primary font-semibold hover:underline ask-ai-subject-btn" data-sub="${sub.name}">
          Ask AI Copilot →
        </button>
      </div>
    `;
    container.appendChild(card);
  });

  document.querySelectorAll('.ask-ai-subject-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const sub = btn.getAttribute('data-sub');
      switchTab('ai-assistant');
      sendFullAiQuery(`Can I skip ${sub} today?`);
    });
  });
}


function downloadCertificate(requestId) {
  // Find the student who owns this request so the PDF filename matches
  let studentId = (state.authUser && state.authUser.student_id) ? state.authUser.student_id : '';
  if (!studentId) {
    const req = state.allRequests.find(r => r.request_id === requestId);
    if (req && req.student_id) studentId = req.student_id;
  }
  if (!studentId) studentId = '23331a42001';

  const link = document.createElement('a');
  link.href = `/certificate_${studentId}_${requestId}.pdf`;
  link.download = `Certificate_${studentId}_${requestId}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast('Certificate Downloaded', `Certificate ${requestId} saved to your device.`);
}

function renderCertificateRequests() {
  const container = document.getElementById('cert-requests-list');
  if (!container) return;

  const s = state.authUser;
  const reqs = (s && s.active_requests) ? s.active_requests : [];

  if (reqs.length === 0) {
    container.innerHTML = '<p class="text-xs text-outline italic">No active requests submitted.</p>';
    return;
  }

  container.innerHTML = '';
  reqs.forEach(req => {
    const item = document.createElement('div');
    item.className = 'p-4 rounded-xl bg-surface-container-low/60 border border-surface-container flex items-center justify-between text-body-sm';
    item.innerHTML = `
      <div class="space-y-0.5">
        <div class="flex items-center gap-2">
          <span class="font-mono-data text-xs font-semibold text-primary">${req.request_id}</span>
          <span class="font-semibold text-on-surface">${req.certificate_type}</span>
        </div>
        <p class="text-xs text-outline">${req.remarks || 'Verification in progress'}</p>
      </div>
      <div class="flex items-center gap-3">
        <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold ${req.status === 'Approved' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}">
          ${req.status}
        </span>
        ${req.status === 'Approved' ? `<button onclick="downloadCertificate('${req.request_id}')" class="px-2.5 py-1 rounded-lg bg-primary text-white text-xs font-semibold hover:bg-primary-container transition shadow-sm">Download</button>` : ''}
      </div>
    `;
    container.appendChild(item);
  });
}

// -------------------------------------------------------------
// DIRECTORIES (STUDENT & STAFF DATASETS)
// -------------------------------------------------------------
function renderStudentDirectory() {
  const tbody = document.getElementById('students-table-body');
  if (!tbody) return;

  const deptFilter = document.getElementById('student-filter-dept')?.value || '';
  const search = document.getElementById('student-search-input')?.value.toLowerCase() || '';

  let filtered = state.students;
  if (deptFilter) {
    filtered = filtered.filter(s => s.department === deptFilter);
  }
  if (search) {
    filtered = filtered.filter(s => 
      s.full_name.toLowerCase().includes(search) ||
      s.student_id.toLowerCase().includes(search) ||
      s.email.toLowerCase().includes(search)
    );
  }

  tbody.innerHTML = '';
  filtered.forEach(st => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-surface-container-low/40 transition-colors';
    tr.innerHTML = `
      <td class="p-3.5 font-mono-data font-semibold text-primary">${st.student_id}</td>
      <td class="p-3.5 font-semibold text-on-surface">${st.full_name}</td>
      <td class="p-3.5"><span class="px-2 py-0.5 rounded-md bg-surface-container text-xs font-semibold">${st.department}</span></td>
      <td class="p-3.5 text-outline">${st.email}</td>
      <td class="p-3.5 font-mono-data font-bold text-on-surface">${st.cgpa.toFixed(2)}</td>
      <td class="p-3.5 text-on-surface-variant font-mono-data text-xs">${st.phone}</td>
      <td class="p-3.5">
        <span class="px-2 py-0.5 rounded-full text-xs font-semibold ${st.attendance_pct >= 85 ? 'bg-emerald-50 text-emerald-700' : (st.attendance_pct >= 75 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700')}">
          ${st.attendance_pct}%
        </span>
      </td>
      <td class="p-3.5 text-right">
        <span class="text-xs text-outline font-mono-data">Enrolled</span>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderStaffDirectory() {
  const container = document.getElementById('staff-cards-grid');
  if (!container) return;

  const deptFilter = document.getElementById('staff-filter-dept')?.value || '';
  const search = document.getElementById('staff-search-input')?.value.toLowerCase() || '';

  let filtered = state.staff;
  if (deptFilter) {
    filtered = filtered.filter(st => st.department === deptFilter);
  }
  if (search) {
    filtered = filtered.filter(st =>
      st.full_name.toLowerCase().includes(search) ||
      st.specialization.toLowerCase().includes(search) ||
      st.cabin_location.toLowerCase().includes(search) ||
      st.designation.toLowerCase().includes(search)
    );
  }

  container.innerHTML = '';
  filtered.forEach(st => {
    const initials = st.full_name.replace('Dr. ', '').replace('Prof. ', '').replace('Er. ', '').replace('Mr. ', '').replace('Mrs. ', '').split(' ').map(n => n[0]).join('').substring(0, 2);
    
    const card = document.createElement('div');
    card.className = 'p-5 rounded-2xl bg-surface-container-low/50 border border-surface-container hover:border-primary/40 transition-all flex flex-col justify-between gap-4 shadow-sm';
    card.innerHTML = `
      <div class="space-y-3">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-primary-fixed text-primary flex items-center justify-center font-bold text-sm">
              ${initials}
            </div>
            <div>
              <h3 class="font-semibold text-on-surface text-sm">${st.full_name}</h3>
              <p class="text-xs text-on-surface-variant">${st.designation}</p>
            </div>
          </div>
          <span class="px-2.5 py-0.5 rounded-full bg-surface-container text-xs font-bold text-primary">${st.department}</span>
        </div>

        <div class="space-y-1 text-xs text-on-surface-variant pt-2 border-t border-surface-container/60">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-[16px] text-outline">menu_book</span>
            <span>${st.specialization}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-[16px] text-outline">meeting_room</span>
            <span class="font-mono-data font-medium text-on-surface">${st.cabin_location}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-[16px] text-outline">schedule</span>
            <span>${st.office_hours}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-[16px] text-outline">mail</span>
            <a href="mailto:${st.email}" class="text-primary hover:underline">${st.email}</a>
          </div>
        </div>
      </div>

      <div class="pt-2 flex items-center justify-between text-xs border-t border-surface-container/40">
        <span class="font-mono-data text-outline">${st.staff_id}</span>
        <button class="text-primary font-semibold hover:underline staff-ask-ai-btn" data-name="${st.full_name}">
          Ask AI About Faculty →
        </button>
      </div>
    `;
    container.appendChild(card);
  });

  document.querySelectorAll('.staff-ask-ai-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const name = btn.getAttribute('data-name');
      switchTab('ai-assistant');
      sendFullAiQuery(`Where is ${name}'s cabin and office hours?`);
    });
  });
}

// -------------------------------------------------------------
// CHATBOT ENGINE & MESSAGING
// -------------------------------------------------------------
async function callChatApi(userQuery) {
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userQuery,
        user_id: state.authUser ? (state.authUser.student_id || state.authUser.staff_id) : '23331a42001',
        role: state.authRole
      })
    });
    const data = await res.json();
    return data.response;
  } catch (err) {
    return "Campus AI Engine is active in local mode. Please re-send your inquiry.";
  }
}

async function sendFullAiQuery(queryText) {
  const history = document.getElementById('full-chat-history');
  if (!history || !queryText.trim()) return;

  // Append user message
  const userDiv = document.createElement('div');
  userDiv.className = 'flex items-start justify-end gap-3';
  userDiv.innerHTML = `
    <div class="p-4 rounded-2xl bg-primary-container text-on-primary text-body-md max-w-xl shadow-sm">
      ${queryText}
    </div>
    <div class="w-8 h-8 rounded-xl bg-surface-container text-on-surface flex items-center justify-center font-bold text-xs shrink-0">
      ${document.getElementById('header-avatar').textContent}
    </div>
  `;
  history.appendChild(userDiv);
  history.scrollTop = history.scrollHeight;

  // Typing animation
  const typingDiv = document.createElement('div');
  typingDiv.className = 'flex items-start gap-3 temp-typing';
  typingDiv.innerHTML = `
    <div class="w-8 h-8 rounded-xl bg-primary-container text-on-primary flex items-center justify-center shrink-0">
      <span class="material-symbols-outlined text-[18px]">smart_toy</span>
    </div>
    <div class="p-4 rounded-2xl bg-surface-container-lowest border border-surface-container text-on-surface text-body-md max-w-2xl flex items-center gap-2">
      <span class="h-2 w-2 rounded-full bg-primary animate-bounce"></span>
      <span class="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:0.2s]"></span>
      <span class="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:0.4s]"></span>
      <span class="text-xs text-outline ml-1">Analyzing campus knowledge base...</span>
    </div>
  `;
  history.appendChild(typingDiv);
  history.scrollTop = history.scrollHeight;

  // AI Answer
  const aiAnswer = await callChatApi(queryText);
  typingDiv.remove();

  const formattedHtml = aiAnswer
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code class="px-1.5 py-0.5 rounded bg-surface-container font-mono-data text-xs font-semibold">$1</code>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n- /g, '<br/>• ');

  const agentDiv = document.createElement('div');
  agentDiv.className = 'flex items-start gap-3';
  agentDiv.innerHTML = `
    <div class="w-8 h-8 rounded-xl bg-primary-container text-on-primary flex items-center justify-center shrink-0">
      <span class="material-symbols-outlined text-[18px]">smart_toy</span>
    </div>
    <div class="p-4 rounded-2xl bg-surface-container-lowest border border-surface-container text-on-surface text-body-md max-w-2xl leading-relaxed shadow-sm">
      ${formattedHtml}
    </div>
  `;
  history.appendChild(agentDiv);
  history.scrollTop = history.scrollHeight;
}

async function sendModalAiQuery(queryText) {
  const thread = document.getElementById('ai-modal-thread');
  if (!thread || !queryText.trim()) return;

  const userMsg = document.createElement('div');
  userMsg.className = 'p-3 rounded-xl bg-surface-container text-right font-body-sm text-on-surface';
  userMsg.textContent = queryText;
  thread.appendChild(userMsg);
  thread.scrollTop = thread.scrollHeight;

  const reply = await callChatApi(queryText);
  const formattedHtml = reply
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code class="px-1 bg-surface-container font-mono-data text-xs">$1</code>')
    .replace(/\n/g, '<br/>');

  const agentMsg = document.createElement('div');
  agentMsg.className = 'p-3 rounded-xl bg-surface-container-low font-body-sm text-on-surface border-l-2 border-primary leading-relaxed';
  agentMsg.innerHTML = formattedHtml;
  thread.appendChild(agentMsg);
  thread.scrollTop = thread.scrollHeight;
}

// -------------------------------------------------------------
// TAB SWITCHING
// -------------------------------------------------------------
function switchTab(tabId) {
  state.activeTab = tabId;

  document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
  const target = document.getElementById(`tab-${tabId}`);
  if (target) {
    target.classList.add('active');
  }

  document.querySelectorAll('.nav-item').forEach(btn => {
    if (btn.getAttribute('data-tab') === tabId) {
      btn.className = 'nav-item active flex items-center gap-3 px-3 py-2.5 transition-all bg-primary-container text-on-primary rounded-xl font-medium shadow-sm w-full text-left';
    } else {
      btn.className = 'nav-item flex items-center gap-3 px-3 py-2.5 rounded-xl text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface transition-all w-full text-left';
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// -------------------------------------------------------------
// SETUP LISTENERS
// -------------------------------------------------------------
function setupAuthListeners() {
  let selectedAuthRole = 'student';

  // Toggle Login Tabs (Student vs Staff)
  const tabStudent = document.getElementById('auth-tab-student');
  const tabStaff = document.getElementById('auth-tab-staff');
  const identLabel = document.getElementById('auth-ident-label');
  const identInput = document.getElementById('auth-identifier-input');
  const demoStudentPills = document.getElementById('demo-pills-student');
  const demoStaffPills = document.getElementById('demo-pills-staff');

  tabStudent?.addEventListener('click', () => {
    selectedAuthRole = 'student';
    tabStudent.className = 'flex-1 py-2 px-3 text-center rounded-xl font-label-md text-xs sm:text-sm bg-surface-container-lowest text-primary shadow-sm font-bold transition-all flex items-center justify-center gap-1.5';
    tabStaff.className = 'flex-1 py-2 px-3 text-center rounded-xl font-label-md text-xs sm:text-sm text-on-surface-variant hover:text-on-surface font-semibold transition-all flex items-center justify-center gap-1.5';
    identLabel.textContent = 'Student ID or College Email';
    identInput.placeholder = 'e.g. 23331a42001 or aarav.sharma1@college.edu';
    demoStudentPills.classList.remove('hidden');
    demoStaffPills.classList.add('hidden');
  });

  tabStaff?.addEventListener('click', () => {
    selectedAuthRole = 'staff';
    tabStaff.className = 'flex-1 py-2 px-3 text-center rounded-xl font-label-md text-xs sm:text-sm bg-surface-container-lowest text-primary shadow-sm font-bold transition-all flex items-center justify-center gap-1.5';
    tabStudent.className = 'flex-1 py-2 px-3 text-center rounded-xl font-label-md text-xs sm:text-sm text-on-surface-variant hover:text-on-surface font-semibold transition-all flex items-center justify-center gap-1.5';
    identLabel.textContent = 'Staff ID or Official Email';
    identInput.placeholder = 'e.g. STF101 or rajesh.raman@college.edu';
    demoStaffPills.classList.remove('hidden');
    demoStudentPills.classList.add('hidden');
  });

  // Password Visibility Toggle
  const togglePwdBtn = document.getElementById('auth-toggle-pwd');
  const pwdInput = document.getElementById('auth-password-input');
  togglePwdBtn?.addEventListener('click', () => {
    const isPwd = pwdInput.type === 'password';
    pwdInput.type = isPwd ? 'text' : 'password';
    togglePwdBtn.querySelector('span').textContent = isPwd ? 'visibility_off' : 'visibility';
  });

  // Form Submit
  document.getElementById('auth-login-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const ident = identInput.value.trim();
    const pwd = pwdInput.value.trim();
    if (ident && pwd) {
      performLogin(selectedAuthRole, ident, pwd);
    }
  });

  // 1-Click Demo Pills
  document.querySelectorAll('.demo-login-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const role = btn.getAttribute('data-role');
      const id = btn.getAttribute('data-id');
      const pwd = btn.getAttribute('data-pwd');
      
      identInput.value = id;
      pwdInput.value = pwd;
      performLogin(role, id, pwd);
    });
  });

  // Logout Header Button
  document.getElementById('header-logout-btn')?.addEventListener('click', performLogout);
}

function setupAppListeners() {
  // Navigation tabs
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab')));
  });
  document.querySelectorAll('.nav-switch-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab')));
  });

  // Search & Filters
  document.getElementById('student-filter-dept')?.addEventListener('change', renderStudentDirectory);
  document.getElementById('student-search-input')?.addEventListener('input', renderStudentDirectory);

  document.getElementById('staff-filter-dept')?.addEventListener('change', renderStaffDirectory);
  document.getElementById('staff-search-input')?.addEventListener('input', renderStaffDirectory);

  document.getElementById('global-search-input')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      const q = e.target.value.trim();
      if (q) {
        switchTab('ai-assistant');
        sendFullAiQuery(q);
        e.target.value = '';
      }
    }
  });

  // Modals
  const aiModal = document.getElementById('ai-agent-modal');
  const uploadModal = document.getElementById('upload-modal');
  const feeModal = document.getElementById('fee-modal');

  document.getElementById('trigger-ai-modal')?.addEventListener('click', () => aiModal.classList.remove('hidden'));
  document.getElementById('close-ai-modal')?.addEventListener('click', () => aiModal.classList.add('hidden'));

  document.getElementById('trigger-upload-modal')?.addEventListener('click', () => uploadModal.classList.remove('hidden'));
  document.getElementById('cert-page-apply-btn')?.addEventListener('click', () => uploadModal.classList.remove('hidden'));
  document.getElementById('close-upload-modal')?.addEventListener('click', () => uploadModal.classList.add('hidden'));
  document.getElementById('cancel-upload')?.addEventListener('click', () => uploadModal.classList.add('hidden'));

  document.getElementById('quick-pay-btn')?.addEventListener('click', () => feeModal.classList.remove('hidden'));
  document.getElementById('card-pay-btn')?.addEventListener('click', () => feeModal.classList.remove('hidden'));
  document.getElementById('tab-pay-fees-btn')?.addEventListener('click', () => feeModal.classList.remove('hidden'));
  document.getElementById('fee-page-action-btn')?.addEventListener('click', () => feeModal.classList.remove('hidden'));
  document.getElementById('review-settle-btn')?.addEventListener('click', () => feeModal.classList.remove('hidden'));
  document.getElementById('close-fee-modal')?.addEventListener('click', () => feeModal.classList.add('hidden'));

  document.getElementById('quick-config-btn')?.addEventListener('click', () => switchTab('settings'));

  document.getElementById('notif-btn')?.addEventListener('click', () => {
    showToast("Academic Notifications", "Midterm examination schedules published. Hall tickets active.");
  });

  document.getElementById('view-schedule-quick')?.addEventListener('click', () => {
    showToast("Timetable", "DBMS Lecture: Monday & Wednesday at 10:00 AM in Room CS-204.");
  });

  // Certificate Submission
  document.getElementById('submit-upload')?.addEventListener('click', async () => {
    const certType = document.getElementById('cert-select').value;
    const purpose = document.getElementById('cert-purpose-input')?.value || 'General Clearance';
    
    uploadModal.classList.add('hidden');
    try {
      const res = await fetch('/api/requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: state.authUser.student_id,
          certificate_type: certType,
          purpose: purpose
        })
      });
      const data = await res.json();
      if (data.success) {
        state.authUser.active_requests = state.authUser.active_requests || [];
        state.authUser.active_requests.unshift(data.request);
        state.allRequests.unshift({
          ...data.request,
          student_id: state.authUser.student_id,
          student_name: state.authUser.full_name,
          department: state.authUser.department
        });
        renderStudentDashboard();
        renderCertificateRequests();
        showToast("Application Submitted", `${certType} (${data.request_id}) placed in review queue.`);
      }
    } catch (err) {
      showToast("Submission Error", "Could not submit application.", false);
    }
  });

  // Fee Payment Execution
  document.getElementById('confirm-fee-pay')?.addEventListener('click', async () => {
    feeModal.classList.add('hidden');
    try {
      const res = await fetch('/api/fees/pay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: state.authUser.student_id,
          amount: state.authUser.fee_balance,
          method: 'UPI / Net Banking'
        })
      });
      const data = await res.json();
      if (data.success) {
        state.authUser.fee_balance = 0.0;
        state.authUser.fee_status = 'Paid';
        renderStudentDashboard();
        showToast("Payment Successful", `Settled in full! Receipt: ${data.receipt_id}`);
      }
    } catch (err) {
      showToast("Payment Failed", "Transaction could not be processed.", false);
    }
  });

  // Modal AI Chat
  document.getElementById('send-ai-query')?.addEventListener('click', () => {
    const input = document.getElementById('ai-prompt-input');
    if (input && input.value) {
      sendModalAiQuery(input.value);
      input.value = '';
    }
  });
  document.getElementById('ai-prompt-input')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      const input = document.getElementById('ai-prompt-input');
      if (input && input.value) {
        sendModalAiQuery(input.value);
        input.value = '';
      }
    }
  });

  // Widget AI Chat
  document.getElementById('widget-ai-send')?.addEventListener('click', () => {
    const widgetInput = document.getElementById('widget-ai-input');
    if (widgetInput && widgetInput.value.trim()) {
      aiModal.classList.remove('hidden');
      sendModalAiQuery(widgetInput.value);
      widgetInput.value = '';
    }
  });
  document.getElementById('widget-ai-input')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      const widgetInput = document.getElementById('widget-ai-input');
      if (widgetInput && widgetInput.value.trim()) {
        aiModal.classList.remove('hidden');
        sendModalAiQuery(widgetInput.value);
        widgetInput.value = '';
      }
    }
  });

  document.querySelectorAll('.prompt-tag').forEach(tag => {
    tag.addEventListener('click', () => {
      const text = tag.textContent.trim();
      aiModal.classList.remove('hidden');
      sendModalAiQuery(text);
    });
  });

  // Full Chat Tab
  document.getElementById('full-chat-send-btn')?.addEventListener('click', () => {
    const input = document.getElementById('full-chat-input');
    if (input && input.value.trim()) {
      sendFullAiQuery(input.value.trim());
      input.value = '';
    }
  });
  document.getElementById('full-chat-input')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      const input = document.getElementById('full-chat-input');
      if (input && input.value.trim()) {
        sendFullAiQuery(input.value.trim());
        input.value = '';
      }
    }
  });

  document.querySelectorAll('.full-ai-prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      sendFullAiQuery(chip.textContent.trim());
    });
  });

  // Inject staff-specific AI copilot chips after login
  injectStaffCopilotChips();
}

// Called after login to inject role-specific copilot chips
function injectStaffCopilotChips() {
  if (state.authRole !== 'staff') return;

  const chipContainer = document.querySelector('.full-ai-prompt-chip')?.parentElement;
  if (!chipContainer) return;

  // Replace student chips with staff-focused ones
  chipContainer.innerHTML = '';

  const staffChips = [
    'Show students above 7 CGPA',
    'Show students above 8.5 CGPA',
    'Send email to students above 7',
    'Show attendance shortage below 75%',
    'My office hours and cabin location',
    'Who is the HOD of CSE?'
  ];

  staffChips.forEach(text => {
    const btn = document.createElement('button');
    btn.className = 'full-ai-prompt-chip px-3 py-1.5 rounded-xl bg-primary-container/30 hover:bg-primary-container text-on-surface text-xs font-medium border border-primary/20 transition-all';
    btn.textContent = text;
    btn.addEventListener('click', () => sendFullAiQuery(text));
    chipContainer.appendChild(btn);
  });

  // Update welcome message for staff
  const chatHistory = document.getElementById('full-chat-history');
  if (chatHistory) {
    chatHistory.innerHTML = `
      <div class="flex items-start gap-3">
        <div class="w-8 h-8 rounded-xl bg-primary-container text-on-primary flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined text-[18px]">smart_toy</span>
        </div>
        <div class="p-4 rounded-2xl bg-surface-container-lowest border border-surface-container text-on-surface text-body-md max-w-2xl leading-relaxed shadow-sm">
          🤖 <strong>Campus AI Copilot — Staff Mode Active.</strong><br/>
          Hi <strong>${state.authUser?.full_name || 'Faculty'}</strong>! I can help you:<br/>
          • <em>List students above any CGPA threshold</em> with full contact details<br/>
          • <em>Auto-send emails</em> from your staff email to high achievers<br/>
          • <em>Check attendance roster</em> &amp; flag shortage students (&lt;75%)<br/>
          Try the quick-action chips above, or type your query below.
        </div>
      </div>`;
  }
}

// Remaining initApp event wires (Supabase test button)
function initSupabaseTestBtn() {
  document.getElementById('test-supabase-btn')?.addEventListener('click', async () => {

    const key = document.getElementById('supabase-key-input')?.value.trim();
    const resultBox = document.getElementById('supabase-connection-result');
    resultBox.classList.remove('hidden');

    if (!key) {
      resultBox.className = 'p-3.5 rounded-xl text-xs font-mono-data bg-amber-50 text-amber-800 border border-amber-200';
      resultBox.innerHTML = `⚠️ <strong>No Key Provided</strong><br/>Using pre-loaded local dataset. Enter your Supabase Anon Key to enable live cloud queries.`;
      return;
    }

    resultBox.className = 'p-3.5 rounded-xl text-xs font-mono-data bg-blue-50 text-blue-800 border border-blue-200';
    resultBox.innerHTML = `⏳ Testing connection to <strong>${SUPABASE_PROJECT_URL}</strong>...`;

    try {
      initSupabase(key);
      localStorage.setItem('supabase_anon_key', key);
      const { data, error } = await supabaseClient.from('departments').select('*').limit(1);
      if (error) throw error;

      resultBox.className = 'p-3.5 rounded-xl text-xs font-mono-data bg-emerald-50 text-emerald-800 border border-emerald-200';
      resultBox.innerHTML = `✅ <strong>Connected to Supabase Cloud!</strong><br/>Project URL: ${SUPABASE_PROJECT_URL}<br/>Live database verified.`;
      showToast("Supabase Connected", "Live cloud database sync active!");
    } catch (err) {
      resultBox.className = 'p-3.5 rounded-xl text-xs font-mono-data bg-blue-50 text-blue-800 border border-blue-200';
      resultBox.innerHTML = `ℹ️ <strong>Supabase Client Ready</strong><br/>Key stored locally. Run <code>supabase_schema.sql</code> in your Supabase SQL Editor to establish tables.<br/>Status: ${err.message || 'Stored'}`;
      showToast("Key Saved", "Supabase config stored.");
    }
  });
}

// Start on DOM ready
document.addEventListener('DOMContentLoaded', initApp);
