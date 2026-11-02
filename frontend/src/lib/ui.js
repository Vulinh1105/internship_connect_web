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
    <h3><a href="${rootPrefix()}src/pages/internship-detail.html?id=${i.id}">${esc(i.title)}</a></h3>
    <div class="muted">${esc(i.company_name || "")} · ${esc(i.location || "Chưa rõ địa điểm")} · Hạn: ${fmtDay(i.deadline)} ${badge(i.status)}</div>
    ${i.description ? `<p>${esc(i.description)}</p>` : ""}
    ${i.requirements ? `<p class="muted"><b>Yêu cầu:</b> ${esc(i.requirements)}</p>` : ""}
    <div class="row">${actionsHtml}</div></div>`;
}

