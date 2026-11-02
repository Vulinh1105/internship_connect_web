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
      ? cvs.map(c => `<div class="row">${esc(c.file_name)} <button class="small" data-download="${c.id}">Xem CV</button> ${c.is_primary ? badge("open").replace("Đang mở", "CV chính") : `<button class="small" data-primary="${c.id}">Đặt làm CV chính</button>`}</div>`).join("")
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
    const download = e.target.closest("[data-download]");
    if (download) return run(() => openFile(`/students/me/cvs/${download.dataset.download}/download`));
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
      const button = e.target.querySelector("button");
      button.disabled = true;
      $("#answer").textContent = "Đang tra cứu tài liệu…";
      try {
        const r = await api("/ai/chat", { method: "POST", body: { question: $("#question").value } });
        const src = r.sources.length ? `<div class="muted">Nguồn: ${r.sources.map(s => esc(s.title)).join(" · ")}</div>` : "";
        $("#answer").innerHTML = `<div class="answer">${esc(r.answer)}</div>${src}`;
      } catch (error) { $("#answer").textContent = error.message; throw error; }
      finally { button.disabled = false; }
    });
  };
  run(loadProfile);
}

