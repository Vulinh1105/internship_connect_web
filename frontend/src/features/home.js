// ===================== Trang chủ =====================
async function pageHome() {
  const data = await api("/internships?page_size=6", { auth: false });
  $("#latest").innerHTML = data.items.length ? data.items.map(i => internshipCard(i)).join("") : `<p class="muted">Chưa có vị trí nào.</p>`;
  $("#searchForm").onsubmit = e => {
    e.preventDefault();
    location.href = "src/pages/internships.html?q=" + encodeURIComponent($("#q").value);
  };
}

