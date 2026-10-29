// Logic giao diện: mỗi trang đặt <body data-page="..."> và được xử lý ở bảng PAGES cuối file.
const $ = (sel, el = document) => el.querySelector(sel);

// Mọi nội dung từ người dùng/server PHẢI qua esc() trước khi chèn vào innerHTML (chống XSS)
function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function toast(msg, isError = false) {
  const t = $("#toast");
  t.textContent = msg; t.style.background = isError ? "#b91c1c" : ""; t.style.color = isError ? "#fff" : "";
  t.style.display = "block";
  clearTimeout(toast._t); toast._t = setTimeout(() => (t.style.display = "none"), 3500);
}
async function run(fn) { try { return await fn(); } catch (e) { toast(e.message, true); } }

const STATUS_LABEL = {
  pending: "Đang chờ", reviewing: "Đang xem xét", accepted: "Được chấp nhận", rejected: "Bị từ chối", withdrawn: "Đã rút",
  open: "Đang mở", closed: "Đã đóng", invited: "Đã mời", confirmed: "Đã xác nhận", declined: "Đã từ chối",
  reschedule_requested: "Đề nghị đổi lịch", cancelled: "Đã hủy",
};
const badge = s => `<span class="badge ${esc(s)}">${esc(STATUS_LABEL[s] || s)}</span>`;
const fmtDay = s => (s ? s.split("-").reverse().join("/") : "—");
const fmtTime = s => (s ? new Date(s).toLocaleString("vi-VN") : "—");

function internshipCard(i, actionsHtml = "") {
  return `<div class="item">
    <h3>${esc(i.title)}</h3>
    <div class="muted">${esc(i.company_name || "")} · ${esc(i.location || "Chưa rõ địa điểm")} · Hạn: ${fmtDay(i.deadline)} ${badge(i.status)}</div>
    ${i.description ? `<p>${esc(i.description)}</p>` : ""}
    ${i.requirements ? `<p class="muted"><b>Yêu cầu:</b> ${esc(i.requirements)}</p>` : ""}
    <div class="row">${actionsHtml}</div></div>`;
}

// ===================== Trang chủ =====================
async function pageHome() {
  const data = await api("/internships?page_size=6", { auth: false });
  $("#latest").innerHTML = data.items.length ? data.items.map(i => internshipCard(i)).join("") : `<p class="muted">Chưa có vị trí nào.</p>`;
  $("#searchForm").onsubmit = e => {
    e.preventDefault();
    location.href = "pages/internships.html?q=" + encodeURIComponent($("#q").value);
  };
}

// ===================== Đăng nhập / đăng ký =====================
async function loginAndGo(email, password) {
  const data = await api("/auth/login", { method: "POST", body: { email, password }, auth: false });
  saveSession(data);
  location.href = rootPrefix() + homeFor(data.user.role);
}
function pageLogin() {
  $("#loginForm").onsubmit = e => { e.preventDefault(); run(() => loginAndGo($("#lEmail").value, $("#lPass").value)); };
  $("#registerForm").onsubmit = e => {
    e.preventDefault();
    run(async () => {
      const body = { email: $("#rEmail").value, password: $("#rPass").value, role: $("#rRole").value };
      await api("/auth/register", { method: "POST", body, auth: false });
      await loginAndGo(body.email, body.password);
    });
  };
}

// ===================== Danh sách vị trí thực tập =====================
function pageInternships() {
  const user = getUser();
  let page = 1;
  $("#q").value = new URLSearchParams(location.search).get("q") || "";

  async function load() {
    const params = new URLSearchParams({ page, page_size: 8 });
    if ($("#q").value.trim()) params.set("q", $("#q").value.trim());
    if ($("#loc").value.trim()) params.set("location", $("#loc").value.trim());
    const data = await api("/internships?" + params, { auth: false });
    $("#list").innerHTML = data.items.length
      ? data.items.map(i => internshipCard(i, user && user.role === "student" ? `<button class="primary small" data-apply="${i.id}" data-title="${esc(i.title)}">Ứng tuyển</button>` : "")).join("")
      : `<p class="muted">Không tìm thấy vị trí phù hợp.</p>`;
    const pages = Math.max(1, Math.ceil(data.total / data.page_size));
    $("#pageInfo").textContent = `Trang ${data.page}/${pages} · ${data.total} vị trí`;
    $("#prev").disabled = page <= 1; $("#next").disabled = page >= pages;
  }
  $("#searchForm").onsubmit = e => { e.preventDefault(); page = 1; run(load); };
  $("#prev").onclick = () => { page--; run(load); };
  $("#next").onclick = () => { page++; run(load); };

  const dlg = $("#applyDialog");
  $("#list").addEventListener("click", e => {
    const btn = e.target.closest("[data-apply]");
    if (!btn) return;
    run(async () => {
      $("#applyTitle").textContent = btn.dataset.title;
      $("#applyForm").dataset.id = btn.dataset.apply;
      $("#cover").value = "";
      let cvs = [];
      try { cvs = await api("/students/me/cvs"); } catch (e) { /* chưa có hồ sơ thì bỏ qua */ }
      $("#cvSelect").innerHTML = `<option value="">Không đính kèm CV</option>` +
        cvs.map(c => `<option value="${c.id}" ${c.is_primary ? "selected" : ""}>${esc(c.file_name)}</option>`).join("");
      dlg.showModal();
    });
  });
  $("#applyCancel").onclick = () => dlg.close();
  $("#applyForm").onsubmit = e => {
    e.preventDefault();
    run(async () => {
      const cv = $("#cvSelect").value;
      await api(`/internships/${e.target.dataset.id}/applications`, {
        method: "POST", body: { cover_letter: $("#cover").value || null, cv_id: cv ? Number(cv) : null },
      });
      dlg.close(); toast("Đã gửi hồ sơ ứng tuyển");
    });
  };
  run(load);
}

// ===================== Sinh viên: hồ sơ, kỹ năng, CV, gợi ý, chatbot =====================
function pageStudent() {
  const fields = ["full_name", "student_code", "major", "gpa", "phone", "profile_summary", "internship_status"];

  async function loadProfile() {
    let s = null;
    try { s = await api("/students/me"); } catch (e) { $("#profileNote").textContent = "Bạn chưa có hồ sơ. Hãy điền họ tên và bấm Lưu."; }
    $("#hasProfile").style.display = s ? "block" : "none";
    if (!s) return;
    $("#profileNote").textContent = "";
    fields.forEach(f => ($("#" + f).value = s[f] ?? (f === "internship_status" ? "not_started" : "")));
    $("#skills").innerHTML = s.skills.length
      ? s.skills.map(k => `<span class="chip">${esc(k.skill_name)}<button data-skill="${k.id}" title="Xóa">×</button></span>`).join("")
      : `<span class="muted">Chưa có kỹ năng.</span>`;
    const cvs = await api("/students/me/cvs");
    $("#cvs").innerHTML = cvs.length
      ? cvs.map(c => `<div class="row">${esc(c.file_name)} ${c.is_primary ? badge("open").replace("Đang mở", "CV chính") : `<button class="small" data-primary="${c.id}">Đặt làm CV chính</button>`}</div>`).join("")
      : `<span class="muted">Chưa có CV.</span>`;
  }

  $("#profileForm").onsubmit = e => {
    e.preventDefault();
    run(async () => {
      const body = {};
      fields.forEach(f => { const v = $("#" + f).value.trim(); if (v !== "") body[f] = f === "gpa" ? Number(v) : v; });
      await api("/students/me", { method: "PUT", body });
      toast("Đã lưu hồ sơ"); await loadProfile();
    });
  };
  $("#skillForm").onsubmit = e => {
    e.preventDefault();
    run(async () => {
      await api("/students/me/skills", { method: "POST", body: { skill_name: $("#skillName").value } });
      $("#skillName").value = ""; await loadProfile();
    });
  };
  $("#skills").onclick = e => {
    const b = e.target.closest("[data-skill]");
    if (b) run(async () => { await api("/students/me/skills/" + b.dataset.skill, { method: "DELETE" }); await loadProfile(); });
  };
  $("#cvForm").onsubmit = e => {
    e.preventDefault();
    run(async () => {
      const file = $("#cvFile").files[0];
      if (!file) throw new Error("Hãy chọn file CV");
      const form = new FormData(); form.append("file", file);
      await api("/students/me/cvs", { method: "POST", form });
      $("#cvFile").value = ""; toast("Đã tải CV lên"); await loadProfile();
    });
  };
  $("#cvs").onclick = e => {
    const b = e.target.closest("[data-primary]");
    if (b) run(async () => { await api(`/students/me/cvs/${b.dataset.primary}/primary`, { method: "PUT" }); await loadProfile(); });
  };

  $("#recoBtn").onclick = () => run(async () => {
    const items = await api("/ai/recommendations?top_k=5");
    $("#reco").innerHTML = items.length
      ? items.map(r => internshipCard(r.internship, `<span class="badge open">Phù hợp ${Math.round(r.score * 100)}%</span>` +
          (r.matched_skills.length ? `<span class="muted">Kỹ năng trùng: ${r.matched_skills.map(esc).join(", ")}</span>` : ""))).join("")
      : `<p class="muted">Hiện chưa có vị trí nào đang mở.</p>`;
  });
  $("#chatForm").onsubmit = e => {
    e.preventDefault();
    run(async () => {
      const r = await api("/ai/chat", { method: "POST", body: { question: $("#question").value } });
      const src = r.sources.length ? `<div class="muted">Nguồn: ${r.sources.map(s => esc(s.title)).join(" · ")}</div>` : "";
      $("#answer").innerHTML = `<div class="answer">${esc(r.answer)}</div>${src}`;
    });
  };
  run(loadProfile);
}

// ===================== Sinh viên: theo dõi đơn & phỏng vấn =====================
function pageApplications() {
  async function load() {
    const apps = await api("/applications/me?page_size=100");
    $("#apps").innerHTML = apps.items.length
      ? `<table><tr><th>Vị trí</th><th>Doanh nghiệp</th><th>Ngày nộp</th><th>Trạng thái</th><th></th></tr>` +
        apps.items.map(a => `<tr><td>${esc(a.internship_title)}</td><td>${esc(a.company_name)}</td><td>${fmtTime(a.applied_at)}</td><td>${badge(a.status)}</td>
          <td>${["pending", "reviewing"].includes(a.status) ? `<button class="small danger" data-withdraw="${a.id}">Rút hồ sơ</button>` : ""}</td></tr>`).join("") + `</table>`
      : `<p class="muted">Bạn chưa ứng tuyển vị trí nào.</p>`;
    const iv = await api("/interviews/me?page_size=100");
    $("#interviews").innerHTML = iv.items.length
      ? iv.items.map(i => `<div class="item"><h3>${esc(i.internship_title)} · ${esc(i.company_name)}</h3>
          <div class="muted">${fmtTime(i.scheduled_at)} · ${esc(i.location)} ${badge(i.status)}</div>
          ${i.note ? `<p>${esc(i.note)}</p>` : ""}${i.student_message ? `<p class="muted">Lời nhắn của bạn: ${esc(i.student_message)}</p>` : ""}
          ${i.status === "invited" ? `<div class="row"><button class="primary small" data-respond="confirm" data-id="${i.id}">Xác nhận</button>
            <button class="small" data-respond="reschedule" data-id="${i.id}">Đề nghị đổi lịch</button>
            <button class="small danger" data-respond="decline" data-id="${i.id}">Từ chối</button></div>` : ""}</div>`).join("")
      : `<p class="muted">Chưa có lịch phỏng vấn.</p>`;
  }
  $("#apps").onclick = e => {
    const b = e.target.closest("[data-withdraw]");
    if (b && confirm("Rút hồ sơ này? Bạn sẽ không ứng tuyển lại được vào cùng vị trí.")) {
      run(async () => { await api(`/applications/${b.dataset.withdraw}/withdraw`, { method: "POST" }); toast("Đã rút hồ sơ"); await load(); });
    }
  };
  $("#interviews").onclick = e => {
    const b = e.target.closest("[data-respond]");
    if (!b) return;
    run(async () => {
      let message = null;
      if (b.dataset.respond === "reschedule") {
        message = prompt("Bạn muốn đổi sang thời gian nào?");
        if (!message) return;
      }
      await api(`/interviews/${b.dataset.id}/respond`, { method: "POST", body: { action: b.dataset.respond, message } });
      toast("Đã gửi phản hồi"); await load();
    });
  };
  run(load);
}

// ===================== Doanh nghiệp =====================
function pageCompany() {
  let currentInternship = null;

  async function loadCompany() {
    let c = null;
    try { c = await api("/companies/me"); } catch (e) { /* chưa có hồ sơ */ }
    $("#companyNote").textContent = c ? "" : "Bạn chưa có hồ sơ doanh nghiệp. Hãy điền và bấm Lưu.";
    $("#needCompany").style.display = c ? "block" : "none";
    ["company_name", "description", "address", "website"].forEach(f => ($("#" + f).value = c ? c[f] ?? "" : ""));
    $("#companyForm").dataset.exists = c ? "1" : "";
    if (c) { await loadInternships(); await loadInterviews(); }
  }
  $("#companyForm").onsubmit = e => {
    e.preventDefault();
    run(async () => {
      const body = {};
      ["company_name", "description", "address", "website"].forEach(f => { const v = $("#" + f).value.trim(); if (v) body[f] = v; });
      await api("/companies" + (e.target.dataset.exists ? "/me" : ""), { method: e.target.dataset.exists ? "PUT" : "POST", body });
      toast("Đã lưu hồ sơ doanh nghiệp"); await loadCompany();
    });
  };

  $("#internshipForm").onsubmit = e => {
    e.preventDefault();
    run(async () => {
      const body = { title: $("#title").value };
      ["description", "requirements", "location", "deadline"].forEach(f => { const v = $("#i_" + f).value.trim(); if (v) body[f] = v; });
      await api("/internships", { method: "POST", body });
      e.target.reset(); toast("Đã đăng tin"); await loadInternships();
    });
  };

  async function loadInternships() {
    const data = await api("/internships/mine?page_size=100");
    $("#myInternships").innerHTML = data.items.length
      ? data.items.map(i => internshipCard(i, `<button class="small" data-view="${i.id}" data-title="${esc(i.title)}">Xem ứng viên</button>` +
          (i.status === "open" ? `<button class="small danger" data-close="${i.id}">Đóng tin</button>` : ""))).join("")
      : `<p class="muted">Chưa có tin nào.</p>`;
  }
  $("#myInternships").onclick = e => {
    const v = e.target.closest("[data-view]"), c = e.target.closest("[data-close]");
    if (v) run(() => loadApplicants(Number(v.dataset.view), v.dataset.title));
    if (c && confirm("Đóng tin này? Sinh viên sẽ không ứng tuyển được nữa.")) {
      run(async () => { await api(`/internships/${c.dataset.close}/close`, { method: "POST" }); await loadInternships(); });
    }
  };

  async function loadApplicants(id, title) {
    currentInternship = { id, title };
    const data = await api(`/internships/${id}/applications?page_size=100`);
    $("#applicantsTitle").textContent = "Ứng viên: " + title;
    $("#applicants").innerHTML = data.items.length
      ? `<table><tr><th>Sinh viên</th><th>Kỹ năng</th><th>Thư giới thiệu</th><th>Trạng thái</th><th>Thao tác</th></tr>` +
        data.items.map(a => {
          const s = a.student || {};
          const canDecide = ["pending", "reviewing"].includes(a.status);
          return `<tr><td><b>${esc(s.full_name)}</b><br><span class="muted">${esc(s.major || "")} · GPA ${esc(s.gpa ?? "—")}<br>${esc(s.phone || "")}</span></td>
            <td>${(s.skills || []).map(k => `<span class="chip">${esc(k)}</span>`).join(" ")}</td>
            <td>${esc(a.cover_letter || "")}</td><td>${badge(a.status)}</td>
            <td><div class="row">
              ${a.cv_id ? `<button class="small" data-cv="${a.id}">Xem CV</button>` : ""}
              ${a.status === "pending" ? `<button class="small" data-status="reviewing" data-id="${a.id}">Xem xét</button>` : ""}
              ${canDecide ? `<button class="small primary" data-status="accepted" data-id="${a.id}">Chấp nhận</button>
                <button class="small danger" data-status="rejected" data-id="${a.id}">Từ chối</button>
                <button class="small" data-invite="${a.id}" data-name="${esc(s.full_name)}">Mời phỏng vấn</button>` : ""}
            </div></td></tr>`;
        }).join("") + `</table>`
      : `<p class="muted">Chưa có ứng viên.</p>`;
    $("#applicantsCard").style.display = "block";
  }
  $("#applicants").onclick = e => {
    const st = e.target.closest("[data-status]"), cv = e.target.closest("[data-cv]"), inv = e.target.closest("[data-invite]");
    if (st) run(async () => { await api(`/applications/${st.dataset.id}/status`, { method: "PATCH", body: { status: st.dataset.status } }); await loadApplicants(currentInternship.id, currentInternship.title); });
    if (cv) run(() => openFile(`/applications/${cv.dataset.cv}/cv`));
    if (inv) { $("#invName").textContent = inv.dataset.name; $("#inviteForm").dataset.app = inv.dataset.invite; $("#inviteDialog").showModal(); }
  };

  $("#inviteCancel").onclick = () => $("#inviteDialog").close();
  $("#inviteForm").onsubmit = e => {
    e.preventDefault();
    run(async () => {
      await api("/interviews", { method: "POST", body: {
        application_id: Number(e.target.dataset.app), scheduled_at: $("#when").value,
        location: $("#where").value, note: $("#iv_note").value || null } });
      $("#inviteDialog").close(); e.target.reset(); toast("Đã gửi lời mời phỏng vấn");
      await loadApplicants(currentInternship.id, currentInternship.title); await loadInterviews();
    });
  };

  async function loadInterviews() {
    const iv = await api("/interviews/me?page_size=100");
    $("#interviews").innerHTML = iv.items.length
      ? iv.items.map(i => `<div class="item"><h3>${esc(i.student_name)} · ${esc(i.internship_title)}</h3>
          <div class="muted">${fmtTime(i.scheduled_at)} · ${esc(i.location)} ${badge(i.status)}</div>
          ${i.student_message ? `<p class="muted">Sinh viên nhắn: ${esc(i.student_message)}</p>` : ""}
          ${i.status !== "cancelled" ? `<div class="row"><button class="small" data-resched="${i.id}">Đổi lịch</button><button class="small danger" data-cancel="${i.id}">Hủy lịch</button></div>` : ""}</div>`).join("")
      : `<p class="muted">Chưa có lịch phỏng vấn.</p>`;
  }
  $("#interviews").onclick = e => {
    const c = e.target.closest("[data-cancel]"), r = e.target.closest("[data-resched]");
    if (c && confirm("Hủy lịch phỏng vấn này?")) run(async () => { await api(`/interviews/${c.dataset.cancel}/cancel`, { method: "POST" }); await loadInterviews(); });
    if (r) run(async () => {
      const when = prompt("Thời gian mới (định dạng 2026-11-20T09:00):");
      if (!when) return;
      await api(`/interviews/${r.dataset.resched}`, { method: "PATCH", body: { scheduled_at: when } });
      toast("Đã đổi lịch, sinh viên cần xác nhận lại"); await loadInterviews();
    });
  };
  run(loadCompany);
}

// ===================== Khởi động =====================
const PAGES = {
  home: { fn: pageHome }, login: { fn: pageLogin },
  internships: { fn: pageInternships }, student: { fn: pageStudent, roles: ["student"] },
  applications: { fn: pageApplications, roles: ["student"] }, company: { fn: pageCompany, roles: ["company"] },
};
document.addEventListener("DOMContentLoaded", () => {
  renderNav();
  const page = PAGES[document.body.dataset.page];
  if (!page) return;
  if (page.roles && !requireRole(page.roles)) return;
  run(async () => page.fn());
});
