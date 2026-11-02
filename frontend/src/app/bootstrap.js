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
