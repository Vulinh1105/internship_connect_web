// ===================== Doanh nghiệp =====================
function pageCompany() {
  let currentInternship = null;
  let editingId = null;
  let myInternships = [];
  function resetEditor() {
    editingId = null;
    $("#internshipForm").reset();
    $("#internshipFormTitle").textContent = "Đăng tin thực tập";
    $("#saveInternship").textContent = "Đăng tin";
    $("#cancelEdit").hidden = true;
  }
  $("#cancelEdit").onclick = resetEditor;

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
      await api(editingId ? `/internships/${editingId}` : "/internships", { method: editingId ? "PUT" : "POST", body });
      toast("Đã lưu tin và gửi kiểm duyệt"); resetEditor(); await loadInternships();
    });
  };

  async function loadInternships() {
    const data = await api("/internships/mine?page_size=100");
    myInternships = data.items;
    $("#myInternships").innerHTML = data.items.length
      ? data.items.map(i => internshipCard(i, `<p>Kiểm duyệt: ${esc(i.moderation_status)}${i.rejection_reason ? " · " + esc(i.rejection_reason) : ""}</p><p>${esc(i.auto_flags || "")}</p><button class="small danger" data-delete-post="${i.id}">Xóa tin</button><button class="small" data-edit="${i.id}">Sửa tin</button><button class="small" data-view="${i.id}" data-title="${esc(i.title)}">Xem ứng viên</button>` +
          (i.status === "open" ? `<button class="small danger" data-close="${i.id}">Đóng tin</button>` : ""))).join("")
      : `<p class="muted">Chưa có tin nào.</p>`;
  }
  $("#myInternships").onclick = e => {
    const del = e.target.closest("[data-delete-post]");
    if (del && confirm("Xóa bài đăng? Lịch sử ứng tuyển được giữ lại.")) {
      run(async () => { await api(`/internships/${del.dataset.deletePost}`, {method: "DELETE"}); await loadInternships(); });
      return;
    }
    const edit = e.target.closest("[data-edit]");
    if (edit) {
      const item = myInternships.find(i => i.id === Number(edit.dataset.edit));
      if (!item) return;
      editingId = item.id;
      $("#title").value = item.title;
      ["description", "requirements", "location", "deadline"].forEach(field => $("#i_" + field).value = item[field] || "");
      $("#internshipFormTitle").textContent = "Chỉnh sửa tin thực tập";
      $("#saveInternship").textContent = "Lưu thay đổi";
      $("#cancelEdit").hidden = false;
      $("#internshipForm").scrollIntoView({behavior: "smooth"});
    }
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

