const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = { currentView: "home", agentMode: "ask", loaded: new Set() };

function escapeHtml(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}
function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => element.classList.remove("show"), 2400);
}
async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "请求失败");
  return data;
}

function setView(name) {
  state.currentView = name;
  $$(".view").forEach((view) => view.classList.toggle("active", view.id === `${name}View`));
  $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === name));
  const titles = { home: "知识库概览", search: "全库检索", library: "资料库", inbox: "Inbox", agent: "Agent 工作台", health: "知识库健康度" };
  $("#pageTitle").textContent = titles[name] || "知识库";
  $(".sidebar").classList.remove("open");
  if (name === "search") setTimeout(() => $("#searchInput").focus(), 50);
  if (!state.loaded.has(name)) {
    state.loaded.add(name);
    if (name === "library") loadFileTree();
    if (name === "inbox") loadInbox();
    if (name === "health") loadReports();
  }
}

async function loadStatus() {
  const data = await api("/api/status");
  $("#docCount").textContent = data.markdown_count;
  $("#noteCount").textContent = data.note_count;
  $("#mocCount").textContent = data.moc_count;
  $("#inboxCount").textContent = data.inbox_count;
  $("#navInboxCount").textContent = data.inbox_count;
  $("#indexState").textContent = data.indexed_count ? `${data.indexed_count} 项 · ${data.index_updated?.replace("T", " ")}` : "尚未建立";
  $("#recentFiles").innerHTML = data.recent_files.map((file) => `<button class="file-row" data-path="${escapeHtml(file.path)}"><span><strong>${escapeHtml(file.name)}</strong><small>${escapeHtml(file.path)}</small></span><time>${escapeHtml(file.updated.slice(5).replace("T", " "))}</time></button>`).join("") || '<div class="empty">还没有最近更新的文件。</div>';
}
function formatBytes(value) {
  if (value == null) return "—";
  if (value < 1024) return `${value} B`;
  if (value < 1048576) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1048576).toFixed(1)} MB`;
}
function cleanSnippet(value) { return escapeHtml(value).replaceAll("[", "<mark>").replaceAll("]", "</mark>"); }

async function runSearch(query) {
  const normalized = query.trim();
  if (!normalized) return;
  setView("search");
  $("#searchInput").value = normalized;
  $("#resultMeta").textContent = "正在检索…";
  $("#searchResults").innerHTML = "";
  try {
    const data = await api("/api/search", { method: "POST", body: JSON.stringify({ query: normalized, limit: 20 }) });
    $("#resultMeta").textContent = `“${normalized}” · ${data.count} 条结果`;
    $("#searchResults").innerHTML = data.results.map((result) => `<button class="result-row" data-path="${escapeHtml(result.path)}"><h3>${escapeHtml(result.title)}</h3><p>${cleanSnippet(result.snippet)}</p><footer><span>${escapeHtml(result.kind)}</span><span>${escapeHtml(result.path)}</span></footer></button>`).join("") || '<div class="empty">没有找到直接相关的内容。可以换一个关键词，或去 Inbox 补充材料。</div>';
  } catch (error) { $("#resultMeta").textContent = "检索失败"; toast(error.message); }
}
async function openFile(path) {
  try {
    const data = await api(`/api/file?path=${encodeURIComponent(path)}`);
    $("#readerPath").textContent = data.path;
    $("#readerTitle").textContent = data.name;
    $("#readerContent").textContent = data.content;
    $("#reader").showModal();
  } catch (error) { toast(error.message); }
}
function renderTree(node, depth = 0) {
  if (node.kind === "directory") {
    return `<details class="tree-group"${depth === 0 ? " open" : ""}><summary title="${escapeHtml(node.path)}"><span class="tree-label">${escapeHtml(node.name)}</span></summary><div class="tree-children">${(node.children || []).map((child) => renderTree(child, depth + 1)).join("")}</div></details>`;
  }
  const supported = ["md", "txt", "py", "js", "ts", "tsx", "jsx", "json", "yaml", "yml", "css", "html", "xml", "drawio"].includes(node.kind);
  return `<button class="tree-file" ${supported ? `data-path="${escapeHtml(node.path)}"` : "disabled"} title="${escapeHtml(node.path)}"><span class="file-kind">${escapeHtml(node.kind)}</span><span class="tree-label">${escapeHtml(node.name)}</span></button>`;
}
async function loadFileTree() {
  $("#fileTree").innerHTML = '<div class="empty">正在读取目录…</div>';
  try { const data = await api("/api/files"); $("#fileTree").innerHTML = data.roots.map((root) => renderTree(root)).join(""); }
  catch (error) { $("#fileTree").innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`; }
}
async function loadInbox() {
  try {
    const data = await api("/api/inbox");
    $("#navInboxCount").textContent = data.count;
    $("#inboxItems").innerHTML = data.items.map((item) => `<div class="inbox-row"><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.kind.toUpperCase())} · ${formatBytes(item.size)}</span><time>${escapeHtml(item.updated.replace("T", " "))}</time></div>`).join("") || '<div class="empty">Inbox 已清空，可以放心继续工作。</div>';
  } catch (error) { toast(error.message); }
}
async function previewInbox() {
  const button = $("#previewInboxButton");
  button.disabled = true; button.textContent = "分析中…";
  try {
    const data = await api("/api/inbox/preview", { method: "POST" });
    $("#inboxActions").innerHTML = data.actions.map((action) => `<li>${escapeHtml(action)}</li>`).join("");
    $("#inboxOutput").classList.remove("hidden");
    $("#applyInboxButton").disabled = !data.actions.some((action) => action.startsWith("MOVE"));
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; button.textContent = "预览分流"; }
}
function confirmAction(title, message) {
  return new Promise((resolve) => {
    const dialog = $("#confirmDialog");
    $("#confirmTitle").textContent = title; $("#confirmMessage").textContent = message;
    const finish = (value) => { dialog.close(); resolve(value); };
    $("#cancelConfirm").onclick = () => finish(false); $("#acceptConfirm").onclick = () => finish(true);
    dialog.oncancel = (event) => { event.preventDefault(); finish(false); };
    dialog.showModal();
  });
}
async function runConfirmed(endpoint, title, message) {
  if (!await confirmAction(title, message)) return null;
  return api(endpoint, { method: "POST", body: JSON.stringify({ confirmed: true }) });
}
function setAgentMode(mode) {
  state.agentMode = mode;
  $$(".mode-switch button").forEach((button) => button.classList.toggle("active", button.dataset.agentMode === mode));
  $("#outlineOptions").classList.toggle("hidden", mode !== "outline");
  $("#agentLabel").textContent = mode === "ask" ? "你想从知识库中了解什么？" : "围绕哪个主题生成结构？";
  $("#agentPrompt").placeholder = mode === "ask" ? "例如：我关于 RAG 的资料有哪些，还缺什么？" : "例如：RAG 工程实践";
  $("#agentWriteHint").textContent = mode === "ask" ? "回答会引用本地索引内容" : "将写入 60_Outputs 草案区";
  $("#agentSubmit").textContent = mode === "ask" ? "开始检索" : "生成草案";
}
async function runAgent(event) {
  event.preventDefault();
  const prompt = $("#agentPrompt").value.trim();
  if (!prompt) return;
  const response = $("#agentResponse");
  response.innerHTML = '<span class="response-mark">✦</span><h3>正在整理本地知识…</h3><p>这通常只需要片刻。</p>';
  try {
    if (state.agentMode === "ask") {
      const data = await api("/api/agent/ask", { method: "POST", body: JSON.stringify({ question: prompt, limit: 10 }) });
      response.innerHTML = `<pre>${escapeHtml(data.content)}</pre>`;
    } else {
      if (!await confirmAction("生成大纲草案", `将在 60_Outputs 中创建“${prompt}”草案，是否继续？`)) { response.innerHTML = '<span class="response-mark">✦</span><h3>已取消</h3><p>没有写入任何输出草案。</p>'; return; }
      const kind = document.querySelector('input[name="outlineKind"]:checked').value;
      const data = await api("/api/agent/outline", { method: "POST", body: JSON.stringify({ topic: prompt, kind, limit: 10, confirmed: true }) });
      response.innerHTML = `<span class="response-mark">✓</span><h3>${escapeHtml(data.message)}</h3><p>${escapeHtml(data.path)}</p><button class="outline-button" data-path="${escapeHtml(data.path)}">打开草案</button>`;
      loadStatus();
    }
  } catch (error) { response.innerHTML = `<span class="response-mark">!</span><h3>操作未完成</h3><p>${escapeHtml(error.message)}</p>`; }
}
function reportExcerpt(content) { return content.replace(/^---[\s\S]*?---/, "").replace(/^#.+$/m, "").replace(/[#`*_]/g, "").trim().slice(0, 120); }
async function loadReports() {
  try {
    const [status, data] = await Promise.all([api("/api/status"), api("/api/reports")]);
    $("#healthIndexCount").textContent = `${status.indexed_count} 项`;
    $("#healthIndexTime").textContent = status.index_updated ? `更新于 ${status.index_updated.replace("T", " ")}` : "尚未建立索引";
    $("#reportsGrid").innerHTML = data.reports.map((report) => `<button class="report-item" data-path="${escapeHtml(report.path)}"><span>Report</span><h3>${escapeHtml(report.title)}</h3><p>${escapeHtml(reportExcerpt(report.content))}</p><time>${escapeHtml(report.updated.replace("T", " "))}</time></button>`).join("") || '<div class="empty">还没有健康报告。</div>';
  } catch (error) { toast(error.message); }
}

$$(".nav-item").forEach((item) => item.addEventListener("click", () => setView(item.dataset.view)));
$("#menuButton").addEventListener("click", () => $(".sidebar").classList.toggle("open"));
$("#refreshButton").addEventListener("click", async () => { try { await loadStatus(); toast("状态已刷新"); } catch (error) { toast(error.message); } });
$("#homeSearchForm").addEventListener("submit", (event) => { event.preventDefault(); runSearch($("#homeSearchInput").value); });
$("#searchForm").addEventListener("submit", (event) => { event.preventDefault(); runSearch($("#searchInput").value); });
$(".search-hints").addEventListener("click", (event) => { const button = event.target.closest("[data-query]"); if (button) runSearch(button.dataset.query); });
document.addEventListener("click", (event) => { const file = event.target.closest("[data-path]"); if (file) openFile(file.dataset.path); });
$("#closeReader").addEventListener("click", () => $("#reader").close());
$("#reader").addEventListener("click", (event) => { if (event.target === $("#reader")) $("#reader").close(); });
$("#previewInboxButton").addEventListener("click", previewInbox);
$("#applyInboxButton").addEventListener("click", async () => {
  try {
    const data = await runConfirmed("/api/inbox/apply", "确认归档 Inbox", "文件将移动到资料区，同时创建资料索引和阅读笔记草案。该操作会记录到本地日志。");
    if (!data) return;
    toast(data.message); $("#inboxOutput").classList.add("hidden"); await Promise.all([loadInbox(), loadStatus()]); state.loaded.delete("library");
  } catch (error) { toast(error.message); }
});
$$(".mode-switch button").forEach((button) => button.addEventListener("click", () => setAgentMode(button.dataset.agentMode)));
$("#agentForm").addEventListener("submit", runAgent);
$("#rebuildIndexButton").addEventListener("click", async () => {
  try { const data = await runConfirmed("/api/maintenance/rebuild-index", "重建全文索引", "现有 SQLite 检索缓存会被重新生成，原始文档不会被修改。"); if (!data) return; toast(data.message); await Promise.all([loadStatus(), loadReports()]); } catch (error) { toast(error.message); }
});
$("#runHealthButton").addEventListener("click", async () => {
  const button = $("#runHealthButton");
  try {
    if (!await confirmAction("运行完整体检", "将更新体检报告、双链建议和全文索引，并在操作日志中留下记录。")) return;
    button.disabled = true; button.textContent = "体检中…";
    const data = await api("/api/maintenance/health", { method: "POST", body: JSON.stringify({ confirmed: true }) });
    toast(data.message); await Promise.all([loadStatus(), loadReports()]);
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; button.textContent = "运行完整体检"; }
});

loadStatus().catch((error) => toast(error.message));
