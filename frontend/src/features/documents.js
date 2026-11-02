document.addEventListener("DOMContentLoaded", () => {
  if (!requireRole(["staff", "admin"])) return;
  const status = document.getElementById("documentStatus");
  async function refresh() {
    const items = await api("/documents");
    document.getElementById("documents").innerHTML = items.length ? items.map(d =>
      `<div class="item"><b>${esc(d.original_filename)}</b> <span>${esc(d.status)}</span>
      <button data-index="${d.id}">Lập chỉ mục</button><button data-download="${d.id}">Tải về</button>
      <button data-delete="${d.id}">Xóa</button></div>`).join("") : "Chưa có tài liệu.";
  }
  document.getElementById("documentUpload").onsubmit = e => {
    e.preventDefault();
    run(async () => {
      const form = new FormData();
      form.append("file", document.getElementById("knowledgeFile").files[0]);
      await api("/documents", {method: "POST", form});
      status.textContent = "Đã tải lên. Chọn Lập chỉ mục để đưa tài liệu vào chatbot.";
      e.target.reset();
      await refresh();
    });
  };
  document.getElementById("documents").onclick = e => run(async () => {
    const button = e.target.closest("button");
    if (!button) return;
    if (button.dataset.download) return openFile(`/documents/${button.dataset.download}/download`);
    button.disabled = true;
    try {
      if (button.dataset.index) {
        status.textContent = "Đang xử lý tài liệu…";
        const result = await api(`/documents/${button.dataset.index}/index`, {method: "POST"});
        status.textContent = result.status === "indexed" ? `Đã index ${result.chunk_count} đoạn.` : `Xử lý thất bại: ${result.error || result.status}`;
      }
      if (button.dataset.delete && confirm("Xóa tài liệu và các đoạn đã index?")) {
        await api(`/documents/${button.dataset.delete}`, {method: "DELETE"});
      }
      await refresh();
    } finally { button.disabled = false; }
  });
  run(refresh);
});
