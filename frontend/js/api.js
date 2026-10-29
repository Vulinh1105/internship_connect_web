// Gọi API backend. Mở giao diện tại http://localhost:8000/app/ thì không cần cấu hình gì thêm.
const API_BASE = window.API_BASE || (location.port === "8000" ? "/api" : "http://localhost:8000/api");

function formatError(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) {
    return data.detail.map(d => `${(d.loc || []).slice(1).join(".")}: ${d.msg}`).join("; ");
  }
  return `Lỗi ${status}`;
}

async function api(path, { method = "GET", body = null, form = null, auth = true } = {}) {
  const headers = {};
  const token = localStorage.getItem("token");
  if (auth && token) headers["Authorization"] = "Bearer " + token;
  let payload;
  if (form) payload = form;
  else if (body !== null) { headers["Content-Type"] = "application/json"; payload = JSON.stringify(body); }

  let res;
  try { res = await fetch(API_BASE + path, { method, headers, body: payload }); }
  catch (e) { throw new Error("Không kết nối được máy chủ. Hãy kiểm tra backend đã chạy chưa."); }

  if (res.status === 401 && auth && token) {
    clearSession();
    location.href = rootPrefix() + "pages/login.html";
    throw new Error("Phiên đăng nhập đã hết hạn");
  }
  if (res.status === 204) return null;
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (e) { /* không phải JSON */ }
  if (!res.ok) throw new Error(formatError(data, res.status));
  return data;
}

// Tải file có kèm token (thẻ <a> thường không gửi được header Authorization)
async function openFile(path) {
  const res = await fetch(API_BASE + path, { headers: { Authorization: "Bearer " + localStorage.getItem("token") } });
  if (!res.ok) {
    let msg = `Lỗi ${res.status}`;
    try { msg = formatError(await res.json(), res.status); } catch (e) { /* bỏ qua */ }
    throw new Error(msg);
  }
  const url = URL.createObjectURL(await res.blob());
  window.open(url, "_blank");
}
