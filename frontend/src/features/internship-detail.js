document.addEventListener("DOMContentLoaded", () => {
  renderNav();
  run(async () => {
    try {
      const id = Number(new URLSearchParams(location.search).get("id"));
      if (!Number.isInteger(id) || id <= 0) throw new Error("Đường dẫn tin thực tập không hợp lệ.");
      const item = await api(`/internships/${id}`, {auth: false});
      document.title = item.title + " · Kết nối thực tập NEU";
      const user = getUser();
      const available = item.status === "open" && (!item.deadline || item.deadline >= new Date().toLocaleDateString("en-CA"));
      const applyUrl = `internships.html?q=${encodeURIComponent(item.title)}&apply=${item.id}`;
      $("#internshipDetail").innerHTML = `<p class="muted">${esc(item.company_name)}</p><h1>${esc(item.title)}</h1><p>${badge(item.status)} <span class="muted">${esc(item.location || "Chưa cập nhật địa điểm")} · Hạn ${fmtDay(item.deadline)}</span></p>
        <h2>Mô tả công việc</h2><p class="preserve-lines">${esc(item.description || "Doanh nghiệp chưa bổ sung mô tả.")}</p>
        <h2>Yêu cầu ứng viên</h2><p class="preserve-lines">${esc(item.requirements || "Liên hệ doanh nghiệp để biết thêm chi tiết.")}</p>
        ${available && user?.role === "student" ? `<a class="btn primary" href="${applyUrl}">Ứng tuyển vị trí này</a>` : !user && available ? '<a class="btn primary" href="login.html">Đăng nhập để ứng tuyển</a>' : !available ? '<p class="notice">Tin đã đóng hoặc hết hạn ứng tuyển.</p>' : ""}`;
      const company = await api(`/companies/${item.company_id}`, {auth: false});
      $("#companyDetail").hidden = false;
      $("#companyDetail").innerHTML = `<h2>Về ${esc(company.company_name)}</h2><p class="preserve-lines">${esc(company.description || "")}</p><p class="muted">${esc(company.address || "")}</p><p>${esc(company.website || "")}</p>`;
    } catch (error) { $("#internshipDetail").textContent = error.message; throw error; }
  });
});
