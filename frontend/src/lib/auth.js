// Đăng nhập, phiên làm việc và thanh điều hướng theo vai trò.
function rootPrefix() { return (document.body && document.body.dataset.root) || ""; }

function saveSession(data) {
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("user", JSON.stringify(data.user));
}
function clearSession() { localStorage.removeItem("token"); localStorage.removeItem("user"); }
function getUser() { try { return JSON.parse(localStorage.getItem("user")); } catch (e) { return null; } }

function homeFor(role) {
  if (["staff", "admin"].includes(role)) return "src/pages/dashboard.html";
  if (role === "student") return "src/pages/students.html";
  if (role === "company") return "src/pages/company.html";
  return "src/pages/internships.html";
}

// Chuyển về trang đăng nhập nếu chưa đăng nhập hoặc sai vai trò
function requireRole(roles) {
  const user = getUser();
  if (!user || !localStorage.getItem("token")) { location.href = rootPrefix() + "src/pages/login.html"; return null; }
  if (roles && !roles.includes(user.role)) { location.href = rootPrefix() + homeFor(user.role); return null; }
  return user;
}

function logout() { clearSession(); location.href = rootPrefix() + "src/pages/login.html"; }

function renderNav() {
  const nav = document.getElementById("nav");
  if (!nav) return;
  const r = rootPrefix();
  const user = getUser();
  const links = [[r + "index.html", "Trang chủ"], [r + "src/pages/internships.html", "Vị trí thực tập"]];
  if (user && user.role === "student") links.push([r + "src/pages/students.html", "Hồ sơ & gợi ý"], [r + "src/pages/applications.html", "Đơn ứng tuyển"]);
  if (user && user.role === "company") links.push([r + "src/pages/company.html", "Quản lý tuyển dụng"]);
  if (user && ["staff", "admin"].includes(user.role)) links.push([r + "src/pages/documents.html", "Tài liệu kiến thức"]);
  if (user && ["staff", "admin"].includes(user.role)) links.push([r + "src/pages/dashboard.html", "Quản trị"]);
  if (user) links.push([r + "src/pages/chatbot.html", "Trợ lý AI"]);
  nav.innerHTML = links.map(([href, text]) => `<a href="${href}">${text}</a>`).join("");
  const who = document.createElement("span");
  who.className = "who";
  if (user) {
    who.textContent = `${user.email} (${user.role}) `;
    const btn = document.createElement("button");
    btn.className = "small"; btn.textContent = "Đăng xuất"; btn.onclick = logout;
    who.appendChild(btn);
  } else {
    who.innerHTML = `<a href="${r}src/pages/login.html">Đăng nhập</a>`;
  }
  nav.appendChild(who);
  nav.querySelectorAll("a").forEach(link => {
    if (new URL(link.href).pathname === location.pathname) link.setAttribute("aria-current", "page");
  });
}
