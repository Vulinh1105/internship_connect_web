document.addEventListener("DOMContentLoaded", () => {
  const user = requireRole(["staff", "admin"]);
  if (!user) return;
  renderNav();
  async function summary() {
    const stats = await api("/internships/stats");
    const cells = [[stats.total_internships, "Tin thực tập"], [stats.open_internships, "Tin đang mở"],
      [stats.total_applications, "Đơn ứng tuyển"], [stats.applications_by_status.accepted || 0, "Đã chấp nhận"]];
    $("#metrics").innerHTML = cells.map(([value, label]) => `<div class="metric"><strong>${esc(value)}</strong><span>${esc(label)}</span></div>`).join("");
    const ai = await api("/ai/status");
    $("#aiStatus").textContent = `${ai.provider} · ${ai.chat_model} · ${ai.embedding_model} · ${ai.configured ? "Đã cấu hình API key" : "Chưa cấu hình OPENAI_API_KEY"}`;
  }
  function paginated(kind, path, headers, row) {
    let page = 1;
    async function load() {
      const data = await api(`${path}?page=${page}&page_size=10`);
      $(`#${kind}Records`).innerHTML = data.items.length ? `<table><thead><tr>${headers.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${data.items.map(row).join("")}</tbody></table>` : '<p class="muted">Chưa có dữ liệu.</p>';
      $(`#${kind}Page`).textContent = `Trang ${page} · ${data.total} kết quả`;
      $(`#${kind}Prev`).disabled = page <= 1;
      $(`#${kind}Next`).disabled = page * data.page_size >= data.total;
    }
    $(`#${kind}Prev`).onclick = () => { page--; run(load); };
    $(`#${kind}Next`).onclick = () => { page++; run(load); };
    run(load);
    return load;
  }
  paginated("student", "/students", ["Họ tên", "Mã SV", "Ngành học", "Kỹ năng"], s =>
    `<tr><td>${esc(s.full_name)}</td><td>${esc(s.student_code || "—")}</td><td>${esc(s.major || "—")}</td><td>${s.skills.map(k => esc(k.skill_name)).join(", ")}</td></tr>`);
  paginated("company", "/companies", ["Doanh nghiệp", "Địa chỉ", "Website"], c =>
    `<tr><td>${esc(c.company_name)}</td><td>${esc(c.address || "—")}</td><td>${esc(c.website || "—")}</td></tr>`);
  if (user.role === "admin") {
    $("#userPanel").hidden = false;
    const reload = paginated("user", "/auth/users", ["Email", "Vai trò", "Trạng thái", "Thao tác"], u =>
      `<tr><td>${esc(u.email)}</td><td>${esc(u.role)}</td><td>${u.is_active ? "Hoạt động" : "Đã khóa"}</td><td><button class="small" data-user="${u.id}" data-active="${!u.is_active}" ${u.id === user.id ? "disabled" : ""}>${u.is_active ? "Khóa" : "Mở khóa"}</button></td></tr>`);
    $("#userRecords").onclick = e => {
      const button = e.target.closest("[data-user]");
      if (!button || !confirm("Cập nhật trạng thái tài khoản này?")) return;
      run(async () => {
        await api(`/auth/users/${button.dataset.user}/active`, {method: "PATCH", body: {is_active: button.dataset.active === "true"}});
        await reload();
      });
    };
  }
  run(summary);
});
