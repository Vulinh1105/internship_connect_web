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
    const autoApply = new URLSearchParams(location.search).get("apply");
    if (autoApply && user && user.role === "student") {
      const button = document.querySelector(`[data-apply="${Number(autoApply)}"]`);
      if (button) {
        history.replaceState(null, "", location.pathname);
        button.click();
      }
    }
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

