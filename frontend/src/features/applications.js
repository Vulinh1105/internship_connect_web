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

