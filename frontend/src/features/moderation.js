document.addEventListener("DOMContentLoaded", () => {
  if (!requireRole(["staff", "admin"])) return;
  renderNav();
  let page = 1;
  async function load() {
    const data = await api(`/internships/moderation?page=${page}&page_size=20` + ($("#filter").value ? `&status=${$("#filter").value}` : ""));
    $("#summary").textContent = `Trang ${page} · ${data.total} bài`;
    $("#prev").disabled = page === 1; $("#next").disabled = page * 20 >= data.total;
    $("#posts").innerHTML = data.items.map(i => `<article class="card"><h2>${esc(i.title)}</h2><p>${esc(i.company_name)} · ${esc(i.moderation_status)} · ${esc(i.status)}</p><p>${esc(i.description)}</p><p>Yêu cầu: ${esc(i.requirements)}</p><p>Địa điểm: ${esc(i.location)} · Hạn: ${esc(i.deadline)}</p><p>Cảnh báo tự động: ${esc(i.auto_flags || "Không phát hiện theo bộ quy tắc hiện tại")}</p><p>Lý do từ chối: ${esc(i.rejection_reason || "—")}</p><p>Người duyệt: ${esc(i.reviewed_by || "—")} · ${esc(i.reviewed_at || "")}</p><button data-action="approved" data-id="${i.id}">Duyệt</button> <button data-action="rejected" data-id="${i.id}">Từ chối</button> <button class="danger" data-action="delete" data-id="${i.id}">Xóa</button></article>`).join("") || "Không có bài đăng.";
  }
  $("#posts").onclick = e => {
    const button = e.target.closest("[data-action]"); if (!button) return;
    run(async () => {
      const action = button.dataset.action, id = button.dataset.id;
      if (action === "delete") {
        if (!confirm("Xóa bài đăng và giữ lịch sử ứng tuyển?")) return;
        await api(`/internships/${id}`, {method: "DELETE"});
      } else {
        const reason = action === "rejected" ? prompt("Nhập lý do từ chối:") : null;
        if (action === "rejected" && !reason?.trim()) return;
        if (action === "approved" && !confirm("Xác nhận đã đọc nội dung và các cảnh báo để duyệt bài?")) return;
        await api(`/internships/${id}/review`, {method: "POST", body: {decision: action, reason}});
      }
      await load();
    });
  };
  $("#filter").onchange = () => {page=1; run(load);};
  $("#refresh").onclick = () => run(load);
  $("#prev").onclick = () => {page--; run(load);};
  $("#next").onclick = () => {page++; run(load);};
  run(load);
});
