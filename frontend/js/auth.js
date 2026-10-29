// Đăng nhập, phiên làm việc và thanh điều hướng theo vai trò.
function rootPrefix() { return (document.body && document.body.dataset.root) || ""; }

function saveSession(data) {
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("user", JSON.stringify(data.user));
}
function clearSession() { localStorage.removeItem("token"); localStorage.removeItem("user"); }
function getUser() { try { return JSON.parse(localStorage.getItem("user")); } catch (e) { return null; } }

function homeFor(role) {
  if (role === "student") return "pages/student.html";
  if (role === "company") return "pages/company.html";
  return "pages/internships.html";
}

// Chuyển về trang đăng nhập nếu chưa đăng nhập hoặc sai vai trò
function requireRole(roles) {
  const user = getUser();
  if (!user || !localStorage.getItem("token")) { location.href = rootPrefix() + "pages/login.html"; return null; }
  if (roles && !roles.includes(user.role)) { location.href = rootPrefix() + homeFor(user.role); return null; }
  return user;
}

function logout() { clearSession(); location.href = rootPrefix() + "pages/login.html"; }

function renderNav() {
  const nav = document.getElementById("nav");
  if (!nav) return;
  const r = rootPrefix();
  const user = getUser();
  const links = [[r + "index.html", "Trang chủ"], [r + "pages/internships.html", "Vị trí thực tập"]];
  if (user && user.role === "student") links.push([r + "pages/student.html", "Hồ sơ & gợi ý"], [r + "pages/applications.html", "Đơn ứng tuyển"]);
  if (user && user.role === "company") links.push([r + "pages/company.html", "Quản lý tuyển dụng"]);
  nav.innerHTML = links.map(([href, text]) => `<a href="${href}">${text}</a>`).join("");
  const who = document.createElement("span");
  who.className = "who";
  if (user) {
    who.textContent = `${user.email} (${user.role}) `;
    const btn = document.createElement("button");
    btn.className = "small"; btn.textContent = "Đăng xuất"; btn.onclick = logout;
    who.appendChild(btn);
  } else {
    who.innerHTML = `<a href="${r}pages/login.html">Đăng nhập</a>`;
  }
  nav.appendChild(who);
}
