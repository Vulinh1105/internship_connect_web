// ===================== Đăng nhập / đăng ký =====================
async function loginAndGo(email, password) {
  const data = await api("/auth/login", { method: "POST", body: { email, password }, auth: false });
  saveSession(data);
  location.href = rootPrefix() + homeFor(data.user.role);
}
function pageLogin() {
  $("#loginForm").onsubmit = e => { e.preventDefault(); run(() => loginAndGo($("#lEmail").value, $("#lPass").value)); };
  $("#registerForm").onsubmit = e => {
    e.preventDefault();
    run(async () => {
      const body = { email: $("#rEmail").value, password: $("#rPass").value, role: $("#rRole").value };
      await api("/auth/register", { method: "POST", body, auth: false });
      await loginAndGo(body.email, body.password);
    });
  };
}

