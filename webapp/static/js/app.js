/* SmartAttend -- app.js */
let selectedFile = null;

function showSection(name) {
  ["home","demo","history"].forEach(s => {
    document.getElementById("sec-" + s).classList.toggle("hidden", s !== name);
  });
  document.querySelectorAll(".nav-link").forEach((el, i) => {
    el.classList.toggle("active", ["home","demo","history"][i] === name);
  });
  if (name === "history") loadHistory();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function toast(msg, type) {
  type = type || "ok";
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "toast " + type + " show";
  setTimeout(function(){ el.classList.remove("show"); }, 3200);
}

function showLoad(msg) {
  document.getElementById("loading-msg").textContent = msg || "Running AI pipeline...";
  document.getElementById("loading-overlay").classList.remove("hidden");
}
function hideLoad() {
  document.getElementById("loading-overlay").classList.add("hidden");
}

window.addEventListener("DOMContentLoaded", async function() {
  try {
    const data = await fetch("/api/students").then(function(r){ return r.json(); });
    renderStudentPills(data.students);
    document.getElementById("stat-students").textContent = data.students.length;
    if (data.ml_ready) {
      document.getElementById("ml-badge").classList.remove("hidden");
    }
  } catch(e) { console.error("Init failed:", e); }
});

function renderStudentPills(students) {
  const box = document.getElementById("student-pills");
  box.innerHTML = students.map(function(s) {
    return '<span style="padding:3px 10px;border-radius:999px;background:var(--white);border:1px solid var(--green-border);font-size:0.75rem;font-weight:600;color:var(--green-h)">' + s + '</span>';
  }).join("");
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById("upload-zone").classList.remove("drag");
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith("image/")) setFile(file);
  else toast("Please drop an image file", "err");
}

function handleFile(e) {
  const file = e.target.files[0];
  if (file) setFile(file);
}

function setFile(file) {
  selectedFile = file;
  const reader = new FileReader();
  reader.onload = function(ev) {
    const img = document.getElementById("preview-img");
    img.src = ev.target.result;
    img.classList.remove("hidden");
  };
  reader.readAsDataURL(file);
  document.getElementById("upload-zone").querySelector("h3").textContent = file.name;
  document.getElementById("upload-zone").querySelector("p").textContent =
    Math.round(file.size / 1024) + " KB -- click to change";
  document.getElementById("action-btns").classList.remove("hidden");
  document.getElementById("result-panel").classList.add("hidden");
  toast("Photo ready -- click Mark Attendance!", "ok");
}

function resetUpload() {
  selectedFile = null;
  document.getElementById("file-input").value = "";
  document.getElementById("preview-img").classList.add("hidden");
  document.getElementById("preview-img").src = "";
  document.getElementById("upload-zone").querySelector("h3").textContent = "Drop classroom photo here";
  document.getElementById("upload-zone").querySelector("p").textContent = "or click to select -- JPG, PNG supported";
  document.getElementById("action-btns").classList.add("hidden");
  document.getElementById("result-panel").classList.add("hidden");
}

async function markAttendance() {
  if (!selectedFile) { toast("Select a photo first", "err"); return; }
  const btn = document.getElementById("mark-btn");
  btn.disabled = true;
  showLoad("Detecting faces and matching embeddings...");
  try {
    const fd = new FormData();
    fd.append("photo", selectedFile);
    const res = await fetch("/api/mark-attendance", { method: "POST", body: fd });
    if (!res.ok) throw new Error("Server error " + res.status);
    const data = await res.json();
    hideLoad();
    renderResult(data);
    toast("Done! " + data.total_present + " present, " + data.total_absent + " absent.", "ok");
  } catch(e) {
    hideLoad();
    toast("Error: " + e.message, "err");
  } finally {
    btn.disabled = false;
  }
}

function renderResult(data) {
  const panel = document.getElementById("result-panel");
  panel.classList.remove("hidden");
  const allStudents = data.present.map(function(n){ return {name:n, status:"present"}; })
    .concat(data.absent.map(function(n){ return {name:n, status:"absent"}; }))
    .sort(function(a,b){ return a.name.localeCompare(b.name); });
  const pct = data.total_students > 0 ? Math.round(data.total_present / data.total_students * 100) : 0;

  panel.innerHTML =
    (data.note ? '<div class="note-banner">Warning: ' + data.note + '</div>' : "") +
    '<div class="result-header">' +
      '<h2>Attendance Report &nbsp;<span style="font-size:0.85rem;font-weight:400;color:var(--text-m)">' + data.date + '</span></h2>' +
      '<div class="summary-chips">' +
        '<span class="chip chip-green">Present: ' + data.total_present + '</span>' +
        '<span class="chip chip-red">Absent: ' + data.total_absent + '</span>' +
        '<span class="chip chip-gray">Attendance: ' + pct + '%</span>' +
      '</div></div>' +
    '<div class="table-wrap"><table class="attend-table"><thead><tr><th>#</th><th>Student Name</th><th>Status</th></tr></thead><tbody>' +
    allStudents.map(function(s, i) {
      return '<tr><td><span class="student-num">' + (i+1) + '</span></td>' +
        '<td style="font-weight:600">' + s.name + '</td>' +
        '<td>' + (s.status === "present"
          ? '<span class="status-p">Present</span>'
          : '<span class="status-a">Absent</span>') + '</td></tr>';
    }).join("") +
    '</tbody></table></div>' +
    (data.result_image ? '<div style="margin-top:20px"><div style="font-size:0.8rem;font-weight:700;color:var(--text-m);margin-bottom:8px;text-transform:uppercase;letter-spacing:0.05em">Annotated Result</div><img src="' + data.result_image + '" class="result-img" alt="Result"/></div>' : "") +
    '<div style="margin-top:20px;display:flex;gap:10px;flex-wrap:wrap">' +
      '<button class="btn btn-green btn-sm" onclick="showSection(\'history\')">View History</button>' +
      '<button class="btn btn-outline btn-sm" onclick="exportCSV()">Export CSV</button>' +
      '<button class="btn btn-ghost btn-sm" onclick="resetUpload()">New Photo</button>' +
    '</div>';

  panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadHistory() {
  const box = document.getElementById("history-list");
  box.innerHTML = '<div class="empty"><div class="empty-icon">Loading</div><p>Loading...</p></div>';
  try {
    const data = await fetch("/api/history").then(function(r){ return r.json(); });
    if (!data.length) {
      box.innerHTML = '<div class="empty"><div class="empty-icon">No Data</div><p>No sessions yet. Go to Live Demo to mark attendance.</p></div>';
      return;
    }
    box.innerHTML = data.map(function(s){ return renderHistoryCard(s); }).join("");
  } catch(e) {
    box.innerHTML = '<div class="empty"><div class="empty-icon">Error</div><p>Failed to load history.</p></div>';
  }
}

function renderHistoryCard(s) {
  const present = s.records.filter(function(r){ return r.status === "present"; });
  const absent  = s.records.filter(function(r){ return r.status === "absent"; });
  const pct = s.records.length > 0 ? Math.round(present.length / s.records.length * 100) : 0;
  const rows = s.records.slice().sort(function(a,b){ return a.name.localeCompare(b.name); })
    .map(function(r, i) {
      return '<tr><td><span class="student-num">' + (i+1) + '</span></td>' +
        '<td style="font-weight:600">' + r.name + '</td>' +
        '<td>' + (r.status === "present"
          ? '<span class="status-p">Present</span>'
          : '<span class="status-a">Absent</span>') + '</td></tr>';
    }).join("");

  return '<div class="history-card">' +
    '<div class="history-header" onclick="toggleHistory(this)">' +
      '<span class="history-date">Session: ' + s.date + '</span>' +
      '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
        '<span class="chip chip-green">' + present.length + ' present</span>' +
        '<span class="chip chip-red">' + absent.length + ' absent</span>' +
        '<span class="chip chip-gray">' + pct + '%</span>' +
      '</div></div>' +
    '<div class="history-body">' +
      '<div class="table-wrap"><table class="attend-table">' +
        '<thead><tr><th>#</th><th>Student Name</th><th>Status</th></tr></thead>' +
        '<tbody>' + rows + '</tbody></table></div>' +
      (s.result_image ? '<img src="' + s.result_image + '" class="result-img" alt="Annotated"/>' : "") +
    '</div></div>';
}

function toggleHistory(header) {
  header.nextElementSibling.classList.toggle("open");
}

function exportCSV() {
  window.open("/api/history/export", "_blank");
  toast("Downloading CSV...", "ok");
}