document.addEventListener("DOMContentLoaded", () => {
  if (!requireRole()) return;
  renderNav();
  const messages = $("#messages");
  let started = false;
  run(async () => {
    const status = await api("/ai/status");
    $("#chatStatus").textContent = status.configured ? "Trợ lý đã được cấu hình. Bạn có thể gửi câu hỏi." : "Quản trị viên cần cấu hình kết nối AI trước khi sử dụng chatbot.";
    $("#sendMessage").disabled = !status.configured;
  });
  $("#assistantForm").onsubmit = async e => {
    e.preventDefault();
    const query = $("#message").value.trim();
    if (query.length < 2) return;
    if (!started) { messages.textContent = ""; started = true; }
    const question = document.createElement("div");
    question.className = "chat-message question";
    question.textContent = query;
    messages.appendChild(question);
    const answer = document.createElement("div");
    answer.className = "chat-message answer";
    answer.textContent = "Đang tra cứu tài liệu…";
    messages.appendChild(answer);
    $("#sendMessage").disabled = true;
    $("#message").value = "";
    try {
      const result = await api("/ai/chat", {method: "POST", body: {question: query}});
      answer.textContent = result.answer;
      if (result.sources.length) {
        const sources = document.createElement("p");
        sources.className = "muted";
        sources.textContent = "Nguồn: " + result.sources.map(s => s.title).join(" · ");
        answer.appendChild(sources);
      }
    } catch (error) { answer.textContent = error.message; }
    finally { $("#sendMessage").disabled = false; answer.scrollIntoView({behavior: "smooth", block: "nearest"}); }
  };
});
