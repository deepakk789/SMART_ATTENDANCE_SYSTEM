/* ═══════════════════════════════════════════════
   SmartAttend — app.js  (Part 1: Core + Landing)
   ═══════════════════════════════════════════════ */

/* ── State ────────────────────────────────────── */
const S = { user: null, token: null };

/* ── API helper ───────────────────────────────── */
const api = {
  headers() {
    const h = { "Content-Type": "application/json" };
    if (S.token) h["Authorization"] = "Bearer " + S.token;
    return h;
  },
  async get(path) {
    const r = await fetch("/api" + path, { headers: this.headers() });
    if (!r.ok) throw await r.json();
    return r.json();
  },
  async post(path, body) {
    const r = await fetch("/api" + path, {
      method: "POST", headers: this.headers(),
      body: JSON.stringify(body),
    });
    if (!r.ok) throw await r.json();
    return r.json();
  },
  async upload(path, formData) {
    const h = {};
    if (S.token) h["Authorization"] = "Bearer " + S.token;
    const r = await fetch("/api" + path, { method: "POST", headers: h, body: formData });
    if (!r.ok) throw await r.json();
    return r.json();
  },
  async del(path) {
    const r = await fetch("/api" + path, { method: "DELETE", headers: this.headers() });
    if (!r.ok) throw await r.json();
    return r.json();
  },
  download(path) { window.open("/api" + path, "_blank"); },
};

/* ── Toast ────────────────────────────────────── */
function toast(msg, type = "info") {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => el.classList.remove("show"), 3200);
}

/* ── Loading ──────────────────────────────────── */
function showLoading(msg = "Processing…") {
  document.getElementById("loading-text").textContent = msg;
  document.getElementById("loading-overlay").classList.remove("hidden");
}
function hideLoading() {
  document.getElementById("loading-overlay").classList.add("hidden");
}

/* ── Auth helpers ─────────────────────────────── */
function saveAuth(token, user) {
  S.token = token; S.user = user;
  localStorage.setItem("sa_token", token);
  localStorage.setItem("sa_user", JSON.stringify(user));
  updateNavbar();
}
function loadAuth() {
  const t = localStorage.getItem("sa_token");
  const u = localStorage.getItem("sa_user");
  if (t && u) { S.token = t; S.user = JSON.parse(u); updateNavbar(); }
}
function updateNavbar() {
  const auth = document.getElementById("nav-auth");
  const user = document.getElementById("nav-user");
  const pill = document.getElementById("user-pill");
  if (S.user) {
    auth.classList.add("hidden");
    user.classList.remove("hidden");
    pill.textContent = S.user.name + " · " + S.user.role;
  } else {
    auth.classList.remove("hidden");
    user.classList.add("hidden");
  }
}
async function logout() {
  try { await api.post("/auth/logout", {}); } catch (_) {}
  S.token = null; S.user = null;
  localStorage.removeItem("sa_token");
  localStorage.removeItem("sa_user");
  updateNavbar();
  navigate("/");
}

/* ── Router ───────────────────────────────────── */
function navigate(path) {
  window.location.hash = "#" + path;
}
function router() {
  const hash = window.location.hash.replace("#", "") || "/";
  const parts = hash.split("/").filter(Boolean);
  const page  = parts[0] || "";
  const id    = parts[1] || "";

  if      (page === "")           renderLanding();
  else if (page === "demo")       renderDemo();
  else if (page === "login")      renderLogin();
  else if (page === "register")   renderRegister();
  else if (page === "dashboard")  renderDashboard();
  else if (page === "classroom")  renderClassroom(id);
  else navigate("/");
}
window.addEventListener("hashchange", router);
window.addEventListener("DOMContentLoaded", () => { loadAuth(); router(); });

/* ── Render helpers ───────────────────────────── */
function setApp(html) {
  document.getElementById("app").innerHTML = html;
}

/* ═══════════════════════════════════════════════
   LANDING PAGE
   ═══════════════════════════════════════════════ */
function renderLanding() {
  setApp(`
  <div class="page">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <div class="hero-badge">🤖 Powered by FaceNet + MTCNN</div>
        <h1>Attendance,<br><span class="grad">Automated by AI.</span></h1>
        <p>Stop calling roll. Upload a classroom photo — our AI identifies every student in seconds and logs attendance instantly.</p>
        <div class="hero-actions">
          <button class="btn btn-primary btn-lg" onclick="navigate('/demo')">🔍 Try Live Demo</button>
          <button class="btn btn-ghost btn-lg" onclick="navigate('/register')">Get Started Free</button>
        </div>
        <div class="hero-stats">
          <div class="stat-item"><div class="stat-num grad">94%</div><div class="stat-label">Recognition Accuracy</div></div>
          <div class="stat-item"><div class="stat-num grad">&lt;2s</div><div class="stat-label">Per Photo</div></div>
          <div class="stat-item"><div class="stat-num grad">128D</div><div class="stat-label">Face Embeddings</div></div>
          <div class="stat-item"><div class="stat-num grad">∞</div><div class="stat-label">Classrooms</div></div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="section" style="background:var(--bg2)">
      <div class="container">
        <h2 class="section-title">Everything you need</h2>
        <p class="section-sub">One platform for teachers and students to manage attendance intelligently.</p>
        <div class="features-grid">
          <div class="feature-card">
            <span class="feature-icon">📸</span>
            <h3>One Photo = Full Attendance</h3>
            <p>Upload a single group photo. MTCNN detects every face, FaceNet identifies each student, and attendance is marked — all in under 2 seconds.</p>
          </div>
          <div class="feature-card">
            <span class="feature-icon">🏫</span>
            <h3>Multi-Classroom Support</h3>
            <p>Teachers create classrooms for any subject. Each classroom has its own student dataset, attendance history, and shareable join code.</p>
          </div>
          <div class="feature-card">
            <span class="feature-icon">📊</span>
            <h3>Real-Time Dashboard</h3>
            <p>Students check today's and past attendance instantly. Teachers get a full date-wise breakdown with one-click CSV export.</p>
          </div>
          <div class="feature-card">
            <span class="feature-icon">🎥</span>
            <h3>Easy Student Registration</h3>
            <p>Teachers request a short 20-30 second face video from each student. Our pipeline auto-builds the recognition dataset — no manual work.</p>
          </div>
          <div class="feature-card">
            <span class="feature-icon">🔒</span>
            <h3>Role-Based Access</h3>
            <p>Teachers manage classrooms and mark attendance. Students view only their own records. Secure token-based authentication throughout.</p>
          </div>
          <div class="feature-card">
            <span class="feature-icon">📥</span>
            <h3>CSV Export</h3>
            <p>Download a full date × student attendance matrix as CSV. Paste it into Excel or Google Sheets in one click.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="section">
      <div class="container">
        <h2 class="section-title">How it works</h2>
        <p class="section-sub">From setup to marked attendance in three simple steps.</p>
        <div class="steps">
          <div class="step">
            <div class="step-num">1</div>
            <h4>Teacher Creates Classroom</h4>
            <p>Add students by name. Share the join code. Request a short face video from each student.</p>
          </div>
          <div class="step">
            <div class="step-num">2</div>
            <h4>AI Builds the Dataset</h4>
            <p>Our pipeline extracts frames, detects faces, and generates 128-dimensional FaceNet embeddings automatically.</p>
          </div>
          <div class="step">
            <div class="step-num">3</div>
            <h4>Upload Photo → Done</h4>
            <p>Teacher uploads one group photo. AI matches every face to the database and marks attendance in seconds.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="section" style="background:var(--bg2)">
      <div class="container text-center">
        <h2 class="section-title">Ready to modernise attendance?</h2>
        <p class="section-sub">Explore the live demo without signing up, or create your account now.</p>
        <div class="hero-actions" style="justify-content:center; margin-top:0">
          <button class="btn btn-primary btn-lg" onclick="navigate('/demo')">🔍 Live Demo</button>
          <button class="btn btn-cyan btn-lg"    onclick="navigate('/register')">Create Account</button>
        </div>
      </div>
    </section>
  </div>`);
}

/* ═══════════════════════════════════════════════
   LOGIN PAGE
   ═══════════════════════════════════════════════ */
function renderLogin() {
  if (S.user) { navigate("/dashboard"); return; }
  setApp(`
  <div class="page auth-page">
    <div class="auth-card">
      <h2>Welcome back</h2>
      <p class="sub">Sign in to your SmartAttend account</p>

      <div class="form-group">
        <label class="form-label">Email</label>
        <input id="login-email" class="form-input" type="email" placeholder="you@college.edu" />
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input id="login-pass" class="form-input" type="password" placeholder="••••••••"
               onkeydown="if(event.key==='Enter') doLogin()" />
      </div>
      <button class="btn btn-primary w-full" style="margin-top:8px" onclick="doLogin()">Sign In</button>

      <div style="margin:20px 0;text-align:center;color:var(--text-s);font-size:0.8rem">— or try demo credentials —</div>
      <button class="btn btn-ghost w-full" onclick="quickLogin('deepak@college.edu','teacher123')">
        🎓 Login as Demo Teacher (Deepak Singh)
      </button>

      <p class="auth-footer">No account? <a onclick="navigate('/register')">Create one</a></p>
    </div>
  </div>`);
}

async function quickLogin(email, pass) {
  document.getElementById("login-email").value = email;
  document.getElementById("login-pass").value  = pass;
  await doLogin();
}

async function doLogin() {
  const email    = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-pass").value;
  if (!email || !password) { toast("Fill in all fields", "error"); return; }
  try {
    showLoading("Signing in…");
    const data = await api.post("/auth/login", { email, password });
    saveAuth(data.token, data.user);
    hideLoading();
    toast("Welcome back, " + data.user.name + "!", "success");
    navigate("/dashboard");
  } catch (e) {
    hideLoading();
    toast(e.detail || "Login failed", "error");
  }
}

/* ═══════════════════════════════════════════════
   REGISTER PAGE
   ═══════════════════════════════════════════════ */
function renderRegister() {
  if (S.user) { navigate("/dashboard"); return; }
  setApp(`
  <div class="page auth-page">
    <div class="auth-card">
      <h2>Create account</h2>
      <p class="sub">Join SmartAttend as a teacher or student</p>

      <div class="form-group">
        <label class="form-label">I am a…</label>
        <div class="role-selector">
          <div class="role-btn active" id="role-teacher" onclick="selectRole('teacher')">
            <span class="role-emoji">👨‍🏫</span> Teacher
          </div>
          <div class="role-btn" id="role-student" onclick="selectRole('student')">
            <span class="role-emoji">👨‍🎓</span> Student
          </div>
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Full Name</label>
        <input id="reg-name" class="form-input" type="text" placeholder="Deepak Singh" />
      </div>
      <div class="form-group">
        <label class="form-label">Email</label>
        <input id="reg-email" class="form-input" type="email" placeholder="you@college.edu" />
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input id="reg-pass" class="form-input" type="password" placeholder="Min 6 characters" />
      </div>
      <button class="btn btn-primary w-full" style="margin-top:8px" onclick="doRegister()">Create Account</button>
      <p class="auth-footer">Already have an account? <a onclick="navigate('/login')">Sign in</a></p>
    </div>
  </div>`);
  window._selectedRole = "teacher";
}

function selectRole(role) {
  window._selectedRole = role;
  document.getElementById("role-teacher").classList.toggle("active", role === "teacher");
  document.getElementById("role-student").classList.toggle("active", role === "student");
}

async function doRegister() {
  const name     = document.getElementById("reg-name").value.trim();
  const email    = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-pass").value;
  const role     = window._selectedRole || "student";
  if (!name || !email || !password) { toast("Fill in all fields", "error"); return; }
  if (password.length < 6) { toast("Password must be at least 6 characters", "error"); return; }
  try {
    showLoading("Creating account…");
    const data = await api.post("/auth/register", { name, email, password, role });
    saveAuth(data.token, data.user);
    hideLoading();
    toast("Account created! Welcome, " + data.user.name, "success");
    navigate("/dashboard");
  } catch (e) {
    hideLoading();
    toast(e.detail || "Registration failed", "error");
  }
}

/* -----------------------------------------------
   DEMO PAGE (Guest � no login required)
   ----------------------------------------------- */
async function renderDemo() {
  setApp(`<div class="page detail-page"><p style="color:var(--text-m)">Loading demo�</p></div>`);
  try {
    const data = await api.get("/demo/classroom");
    const { classroom, students, sessions } = data;
    setApp(`
    <div class="page detail-page">
      <div class="demo-banner">
        <p>?? You are viewing a <strong>Guest Demo</strong> of Deepak's classroom. No login required.</p>
        <div style="display:flex;gap:10px;flex-wrap:wrap">
          <button class="btn btn-primary btn-sm" onclick="navigate('/register')">Create Your Account</button>
          <button class="btn btn-ghost btn-sm" onclick="navigate('/login')">Sign In</button>
        </div>
      </div>

      <div class="detail-hero">
        <div>
          <div style="font-size:0.8rem;color:var(--text-m);margin-bottom:8px">DEMO CLASSROOM</div>
          <h1>${classroom.name}</h1>
          <div class="detail-meta" style="margin-top:10px">
            <span><strong>${classroom.subject}</strong></span>
            <span>????? <strong>${classroom.teacher_name}</strong></span>
            <span>?? <strong>${students.length}</strong> students</span>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:10px;align-items:flex-end">
          <div class="code-badge">Join Code: ${classroom.join_code}</div>
          ${classroom.dataset_ready ? '<span class="tag tag-ok">? Dataset Ready</span>' : ''}
        </div>
      </div>

      <div class="tabs">
        <button class="tab active" onclick="switchTab(event,'demo-students')">?? Students (${students.length})</button>
        <button class="tab" onclick="switchTab(event,'demo-sessions')">?? Attendance History</button>
      </div>

      <div id="demo-students" class="tab-panel active">
        <div class="students-list">
          ${students.map(s => `
          <div class="student-row">
            <span class="student-name">?? ${s.name}</span>
            <div class="student-tags">
              ${s.dataset_built ? '<span class="tag tag-ok">? In Dataset</span>' : '<span class="tag tag-warn">Pending</span>'}
            </div>
          </div>`).join('')}
        </div>
      </div>

      <div id="demo-sessions" class="tab-panel">
        <div class="attend-sessions">
          ${sessions.length ? sessions.map(s => renderSessionCard(s)).join('') : '<p style="color:var(--text-m)">No sessions yet.</p>'}
        </div>
      </div>
    </div>`);

    // Bind accordion toggles
    bindSessionToggles();
  } catch (e) {
    setApp(`<div class="page detail-page"><p style="color:var(--rose)">Failed to load demo: ${e.detail||e}</p></div>`);
  }
}

/* -----------------------------------------------
   DASHBOARD
   ----------------------------------------------- */
async function renderDashboard() {
  if (!S.user) { navigate("/login"); return; }
  setApp(`<div class="page dash-page"><p style="color:var(--text-m)">Loading�</p></div>`);
  try {
    const classrooms = await api.get("/classrooms");
    const isTeacher  = S.user.role === "teacher";

    const cardsHtml = classrooms.length
      ? classrooms.map(c => `
        <div class="classroom-card" onclick="navigate('/classroom/${c.id}')">
          <div class="cc-subject">${c.subject}</div>
          <div class="cc-name">${c.name}</div>
          <div class="cc-teacher">????? ${c.teacher_name}</div>
          <div class="cc-meta">
            <span class="cc-stat">?? <strong>${c.student_count}</strong> students</span>
            <span class="cc-stat">?? <strong>${c.join_code}</strong></span>
            ${c.dataset_ready ? '<span class="cc-stat">? Ready</span>' : ''}
          </div>
        </div>`).join('')
      : `<div class="empty-state">
           <div class="empty-icon">${isTeacher ? '??' : '??'}</div>
           <p>${isTeacher ? 'No classrooms yet. Create your first one!' : 'You have not joined any classrooms yet.'}</p>
         </div>`;

    setApp(`
    <div class="page dash-page">
      <div class="dash-header">
        <div>
          <h1>Welcome, ${S.user.name} ??</h1>
          <p>${isTeacher ? 'Manage your classrooms and attendance' : 'View your attendance across all classrooms'}</p>
        </div>
        ${isTeacher
          ? `<button class="btn btn-primary" onclick="showCreateClassroom()">+ New Classroom</button>`
          : `<button class="btn btn-cyan" onclick="showJoinClassroom()">Join a Classroom</button>`}
      </div>
      <div class="classrooms-grid">${cardsHtml}</div>
    </div>`);
  } catch (e) {
    toast("Failed to load dashboard", "error");
  }
}

/* -- Create Classroom modal --------------------- */
function showCreateClassroom() {
  document.body.insertAdjacentHTML("beforeend", `
  <div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
    <div class="modal">
      <div class="modal-header">
        <h3>New Classroom</h3>
        <button class="modal-close" onclick="closeModalDirect()">?</button>
      </div>
      <div class="form-group">
        <label class="form-label">Class Name</label>
        <input id="cls-name" class="form-input" placeholder="e.g. B.Tech CS � Section A" />
      </div>
      <div class="form-group">
        <label class="form-label">Subject</label>
        <input id="cls-subj" class="form-input" placeholder="e.g. Computer Science" />
      </div>
      <button class="btn btn-primary w-full mt-2" onclick="doCreateClassroom()">Create</button>
    </div>
  </div>`);
}

async function doCreateClassroom() {
  const name    = document.getElementById("cls-name").value.trim();
  const subject = document.getElementById("cls-subj").value.trim();
  if (!name || !subject) { toast("Fill in all fields", "error"); return; }
  try {
    showLoading("Creating classroom�");
    const c = await api.post("/classrooms", { name, subject });
    hideLoading(); closeModalDirect();
    toast("Classroom created!", "success");
    navigate("/classroom/" + c.id);
  } catch (e) { hideLoading(); toast(e.detail || "Error", "error"); }
}

/* -- Join Classroom modal ----------------------- */
function showJoinClassroom() {
  document.body.insertAdjacentHTML("beforeend", `
  <div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
    <div class="modal">
      <div class="modal-header">
        <h3>Join a Classroom</h3>
        <button class="modal-close" onclick="closeModalDirect()">?</button>
      </div>
      <div class="form-group">
        <label class="form-label">Join Code</label>
        <input id="join-code" class="form-input" placeholder="e.g. CS2024A" />
      </div>
      <button class="btn btn-cyan w-full mt-2" onclick="doJoinClassroom()">Join</button>
    </div>
  </div>`);
}

async function doJoinClassroom() {
  const code = document.getElementById("join-code").value.trim();
  if (!code) { toast("Enter a join code", "error"); return; }
  try {
    showLoading("Joining�");
    const r = await api.post("/classrooms/join", { join_code: code });  // fixed path below
    hideLoading(); closeModalDirect();
    toast("Joined classroom!", "success");
    navigate("/classroom/" + r.classroom_id);
  } catch (e) { hideLoading(); toast(e.detail || "Invalid code", "error"); }
}

/* -- Modal helpers ------------------------------ */
function closeModal(e) {
  if (e.target.id === "modal-overlay") closeModalDirect();
}
function closeModalDirect() {
  const m = document.getElementById("modal-overlay");
  if (m) m.remove();
}

/* -----------------------------------------------
   CLASSROOM DETAIL
   ----------------------------------------------- */
async function renderClassroom(id) {
  if (!S.user) { navigate("/login"); return; }
  setApp(`<div class="page detail-page"><p style="color:var(--text-m)">Loading classroom�</p></div>`);
  try {
    const data = await api.get("/classrooms/" + id);
    const { classroom: c, students, sessions } = data;
    const isTeacher = S.user.role === "teacher" && c.teacher_id === S.user.id;

    setApp(`
    <div class="page detail-page">
      <div class="breadcrumb">
        <a onclick="navigate('/dashboard')">Dashboard</a> / <span>${c.name}</span>
      </div>

      <div class="detail-hero">
        <div>
          <h1>${c.name}</h1>
          <div class="detail-meta" style="margin-top:10px">
            <span><strong>${c.subject}</strong></span>
            <span>????? <strong>${c.teacher_name}</strong></span>
            <span>?? <strong>${students.length}</strong> students</span>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:10px;align-items:flex-end">
          <div class="code-badge">?? ${c.join_code}</div>
          ${c.dataset_ready ? '<span class="tag tag-ok">? Dataset Ready</span>' : '<span class="tag tag-warn">Dataset Pending</span>'}
        </div>
      </div>

      <div class="tabs">
        <button class="tab active" onclick="switchTab(event,'tab-students')">?? Students</button>
        <button class="tab" onclick="switchTab(event,'tab-attendance')">?? Take Attendance</button>
        <button class="tab" onclick="switchTab(event,'tab-history')">?? History</button>
      </div>

      <!-- Students tab -->
      <div id="tab-students" class="tab-panel active">
        ${isTeacher ? `
        <div style="display:flex;gap:10px;margin-bottom:18px;flex-wrap:wrap">
          <button class="btn btn-primary btn-sm" onclick="showAddStudent('${id}')">+ Add Student</button>
        </div>` : ''}
        <div class="students-list" id="students-list">
          ${renderStudentsList(students, id, isTeacher)}
        </div>
      </div>

      <!-- Take Attendance tab -->
      <div id="tab-attendance" class="tab-panel">
        ${isTeacher ? `
        <div class="upload-zone" id="upload-zone"
          ondragover="event.preventDefault();this.classList.add('drag')"
          ondragleave="this.classList.remove('drag')"
          ondrop="handleDrop(event,'${id}')"
          onclick="document.getElementById('photo-input').click()">
          <div class="upload-icon">??</div>
          <h3>Upload Group Photo</h3>
          <p>Drag & drop or click to select a classroom photo<br>AI will detect and identify all students</p>
        </div>
        <input type="file" id="photo-input" accept="image/*" style="display:none"
          onchange="handlePhotoUpload(event,'${id}')"/>
        <div id="attend-result"></div>
        ` : `<p style="color:var(--text-m);padding:20px 0">Only the teacher can mark attendance.</p>`}
      </div>

      <!-- History tab -->
      <div id="tab-history" class="tab-panel">
        <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
          <button class="btn btn-ghost btn-sm" onclick="api.download('/classrooms/${id}/attendance/export')">?? Export CSV</button>
        </div>
        <div class="attend-sessions">
          ${sessions.length ? sessions.map(s => renderSessionCard(s)).join('') : '<p style="color:var(--text-m)">No attendance sessions yet.</p>'}
        </div>
      </div>
    </div>`);

    bindSessionToggles();
  } catch (e) {
    toast("Failed to load classroom", "error");
    navigate("/dashboard");
  }
}

/* -- Student helpers ---------------------------- */
function renderStudentsList(students, cid, isTeacher) {
  if (!students.length) return '<p style="color:var(--text-m)">No students enrolled yet.</p>';
  return students.map(s => `
  <div class="student-row">
    <span class="student-name">?? ${s.student_name}</span>
    <div class="student-tags" style="display:flex;align-items:center;gap:8px">
      ${s.dataset_built ? '<span class="tag tag-ok">? Dataset</span>' :
        s.video_uploaded ? '<span class="tag tag-warn">Processing</span>' :
        '<span class="tag tag-err">No Video</span>'}
      ${isTeacher ? `<button class="btn btn-ghost btn-sm" onclick="showUploadVideo('${cid}','${s.student_name}')">?? Upload Video</button>` : ''}
      ${isTeacher ? `<button class="btn btn-rose btn-sm" onclick="removeStudent('${cid}','${s.student_name}')">?</button>` : ''}
    </div>
  </div>`).join('');
}

function showAddStudent(cid) {
  document.body.insertAdjacentHTML("beforeend", `
  <div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
    <div class="modal">
      <div class="modal-header">
        <h3>Add Student</h3>
        <button class="modal-close" onclick="closeModalDirect()">?</button>
      </div>
      <div class="form-group">
        <label class="form-label">Student Full Name</label>
        <input id="new-student-name" class="form-input" placeholder="As in the face dataset" />
      </div>
      <button class="btn btn-primary w-full mt-2" onclick="doAddStudent('${cid}')">Add</button>
    </div>
  </div>`);
}

async function doAddStudent(cid) {
  const name = document.getElementById("new-student-name").value.trim();
  if (!name) { toast("Enter a name", "error"); return; }
  try {
    await api.post("/classrooms/" + cid + "/students", { student_name: name });
    toast("Student added!", "success");
    closeModalDirect();
    renderClassroom(cid);
  } catch (e) { toast(e.detail || "Error", "error"); }
}

async function removeStudent(cid, name) {
  if (!confirm("Remove " + name + " from this classroom?")) return;
  try {
    await api.del("/classrooms/" + cid + "/students/" + encodeURIComponent(name));
    toast("Student removed", "info");
    renderClassroom(cid);
  } catch (e) { toast(e.detail || "Error", "error"); }
}

/* -- Video upload ------------------------------- */
function showUploadVideo(cid, studentName) {
  document.body.insertAdjacentHTML("beforeend", `
  <div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
    <div class="modal">
      <div class="modal-header">
        <h3>Upload Face Video � ${studentName}</h3>
        <button class="modal-close" onclick="closeModalDirect()">?</button>
      </div>
      <p style="color:var(--text-m);font-size:0.875rem;margin-bottom:16px">
        Upload a 20-30 second video of <strong>${studentName}</strong> facing the camera.<br>
        The AI pipeline will auto-build the face dataset.
      </p>
      <input type="file" id="vid-input" class="form-input" accept="video/*" />
      <button class="btn btn-emerald w-full mt-2" onclick="doUploadVideo('${cid}','${studentName}')">Upload & Build Dataset</button>
    </div>
  </div>`);
}

async function doUploadVideo(cid, studentName) {
  const file = document.getElementById("vid-input").files[0];
  if (!file) { toast("Select a video file", "error"); return; }
  const fd = new FormData();
  fd.append("video", file);
  try {
    closeModalDirect();
    showLoading("Building face dataset� this may take 1-2 minutes.");
    await api.upload("/classrooms/" + cid + "/students/" + encodeURIComponent(studentName) + "/video", fd);
    hideLoading();
    toast("Dataset built for " + studentName + "!", "success");
    renderClassroom(cid);
  } catch (e) { hideLoading(); toast(e.detail || "Upload failed", "error"); }
}

/* -- Photo upload + attendance ------------------ */
function handleDrop(e, cid) {
  e.preventDefault();
  document.getElementById("upload-zone").classList.remove("drag");
  const file = e.dataTransfer.files[0];
  if (file) processPhoto(file, cid);
}
function handlePhotoUpload(e, cid) {
  const file = e.target.files[0];
  if (file) processPhoto(file, cid);
}
async function processPhoto(file, cid) {
  const fd = new FormData();
  fd.append("photo", file);
  try {
    showLoading("Running AI � detecting & matching faces�");
    const result = await api.upload("/classrooms/" + cid + "/attendance", fd);
    hideLoading();
    const el = document.getElementById("attend-result");
    el.innerHTML = `
    <div class="card card-pad mt-3">
      <h3 style="margin-bottom:16px">?? Attendance Result � ${result.date}</h3>
      ${result.error ? `<p style="color:var(--amber);margin-bottom:12px">? ${result.error}</p>` : ''}
      <div style="display:flex;gap:24px;margin-bottom:20px">
        <div><span class="chip chip-green">? Present: ${result.total_present}</span></div>
        <div><span class="chip chip-red">? Absent: ${result.total_absent}</span></div>
      </div>
      <div class="students-list">
        ${result.present.map(n => `<div class="student-row"><span class="student-name">?? ${n}</span><span class="tag tag-ok">Present</span></div>`).join('')}
        ${result.absent.map(n => `<div class="student-row"><span class="student-name">?? ${n}</span><span class="tag tag-err">Absent</span></div>`).join('')}
      </div>
      ${result.result_image_url ? `<img src="${result.result_image_url}" class="result-img" alt="Annotated result"/>` : ''}
    </div>`;
    toast("Attendance marked!", "success");
  } catch (e) { hideLoading(); toast(e.detail || "Processing failed", "error"); }
}

/* -- Session card + accordion ------------------- */
function renderSessionCard(s) {
  const rows = (s.records || []).map(r =>
    `<tr><td>${r.name}</td><td class="${r.status === 'present' ? 'status-p' : 'status-a'}">${r.status === 'present' ? '? Present' : '? Absent'}</td></tr>`
  ).join('');
  return `
  <div class="session-card">
    <div class="session-header" onclick="toggleSession(this)">
      <span class="session-date">?? ${s.date}</span>
      <div class="session-chips">
        <span class="chip chip-green">? ${s.total_present} present</span>
        <span class="chip chip-red">? ${s.total_absent} absent</span>
        <span style="color:var(--text-s);font-size:0.8rem">?</span>
      </div>
    </div>
    <div class="session-body">
      ${s.result_image_url ? `<img src="${s.result_image_url}" class="result-img" alt="Class photo"/>` : ''}
      <table class="attend-table" style="margin-top:${s.result_image_url?'16px':'0'}">
        <thead><tr><th>Student</th><th>Status</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  </div>`;
}

function toggleSession(header) {
  const body = header.nextElementSibling;
  body.classList.toggle("open");
}
function bindSessionToggles() {
  // Headers already have onclick; nothing extra needed
}

/* -- Tab switcher ------------------------------- */
function switchTab(e, panelId) {
  const tabsEl   = e.target.closest(".tabs");
  const parentEl = tabsEl.parentElement;
  tabsEl.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  parentEl.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
  e.target.classList.add("active");
  document.getElementById(panelId).classList.add("active");
}
