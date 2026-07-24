const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = {
  currentView: "home",
  searchMode: "hybrid",
  agentMode: "ask",
  loaded: new Set(),
  uploadFiles: [],
  directoriesLoaded: false,
  selectedPlanId: null,
  tasks: [],
  editor: null,
  editing: false,
};

function escapeHtml(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}
function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => element.classList.remove("show"), 2600);
}
async function api(path, options = {}) {
  const isForm = options.body instanceof FormData;
  const headers = { ...(options.headers || {}) };
  if (!isForm && options.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "请求失败");
  return data;
}
function formatBytes(value) {
  if (value == null) return "—";
  if (value < 1024) return `${value} B`;
  if (value < 1048576) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1048576).toFixed(1)} MB`;
}

function setView(name) {
  state.currentView = name;
  $$(".view").forEach((view) => view.classList.toggle("active", view.id === `${name}View`));
  $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === name));
  const titles = { home: "知识库概览", search: "全库检索", library: "资料库", inbox: "收件箱", agent: "Agent 工作台", changes: "变更审批", health: "知识库健康度" };
  $("#pageTitle").textContent = titles[name] || "知识库";
  $(".sidebar").classList.remove("open");
  if (name === "search") setTimeout(() => $("#searchInput").focus(), 50);
  if (name === "library") loadFileTree();
  if (name === "inbox") loadInbox();
  if (name === "changes") loadChanges();
  if (name === "health") loadReports();
}

async function loadStatus() {
  const data = await api("/api/status");
  $("#docCount").textContent = data.markdown_count;
  $("#noteCount").textContent = data.note_count;
  $("#mocCount").textContent = data.moc_count;
  $("#inboxCount").textContent = data.inbox_count;
  $("#navInboxCount").textContent = data.inbox_count;
  const vectorReady = data.vector_indexed_count > 0;
  $("#vectorChip").textContent = vectorReady ? `${data.vector_indexed_count} docs` : "未建索引";
  $("#vectorChip").classList.toggle("ready", vectorReady);
  $("#indexState").textContent = vectorReady ? `${data.indexed_count} 关键词 · ${data.vector_indexed_count} 向量` : `${data.indexed_count} 项关键词`;
  $("#recentFiles").innerHTML = data.recent_files.map((file) => `<button class="file-row" data-path="${escapeHtml(file.path)}"><span><strong>${escapeHtml(file.name)}</strong><small>${escapeHtml(file.path)}</small></span><time>${escapeHtml(file.updated.slice(5).replace("T", " "))}</time></button>`).join("") || '<div class="empty">还没有最近更新的文件。</div>';
  return data;
}

function cleanSnippet(value) {
  return escapeHtml(value).replaceAll("[", "<mark>").replaceAll("]", "</mark>");
}
async function runSearch(query) {
  const normalized = query.trim();
  if (!normalized) return;
  setView("search");
  $("#searchInput").value = normalized;
  $("#resultMeta").textContent = "正在检索…";
  $("#searchResults").innerHTML = "";
  $("#searchWarning").classList.add("hidden");
  try {
    const data = await api("/api/search", { method: "POST", body: JSON.stringify({ query: normalized, limit: 20, mode: state.searchMode }) });
    const modeNames = { hybrid: "混合检索", semantic: "语义检索", keyword: "关键词检索" };
    $("#resultMeta").textContent = `“${normalized}” · ${data.count} 条结果 · ${modeNames[data.mode]}`;
    if (data.warning) { $("#searchWarning").textContent = data.warning; $("#searchWarning").classList.remove("hidden"); }
    $("#searchResults").innerHTML = data.results.map((result) => `<button class="result-row" data-path="${escapeHtml(result.path)}"><h3>${escapeHtml(result.title)}</h3><p>${cleanSnippet(result.snippet)}</p><footer><span class="source-badge">${escapeHtml(result.source || data.mode)}</span><span>${escapeHtml(result.kind)}</span>${result.semantic_score != null || result.score != null ? `<span>score ${escapeHtml(result.semantic_score ?? Number(result.score).toFixed(4))}</span>` : ""}<span>${escapeHtml(result.path)}</span></footer></button>`).join("") || '<div class="empty">没有找到直接相关的内容。可以换一个表述，或上传新的材料。</div>';
  } catch (error) {
    $("#resultMeta").textContent = "检索失败";
    $("#searchWarning").textContent = error.message;
    $("#searchWarning").classList.remove("hidden");
  }
}

async function openFile(path, endpoint = "/api/file") {
  if (endpoint === "/api/file" && /\.pdf$/i.test(path)) { openPdf(path); return; }
  try {
    const separator = endpoint.includes("?") ? "&" : "?";
    const parameter = endpoint === "/api/wiki" ? "title" : "path";
    const data = await api(`${endpoint}${separator}${parameter}=${encodeURIComponent(path)}`);
    exitEditMode();
    $("#readerPdf").classList.add("hidden");
    $("#readerPdf").removeAttribute("src");
    $("#readerPath").textContent = data.path;
    $("#readerTitle").textContent = data.name;
    $("#readerRendered").innerHTML = data.html;
    $("#readerContent").textContent = data.content;
    $("#readerFrontmatter").textContent = data.frontmatter || "";
    $("#readerFrontmatter").classList.toggle("hidden", !data.frontmatter);
    $("#readerRendered").classList.remove("hidden");
    $("#readerContent").classList.add("hidden");
    $("#toggleRawButton").classList.toggle("hidden", !["markdown", "notebook"].includes(data.format));
    state.editor = { path: data.path, format: data.format, mtime: data.mtime };
    $("#editButton").classList.toggle("hidden", !["markdown", "code", "notebook"].includes(data.format));
    $("#reader").showModal();
  } catch (error) { toast(error.message); }
}
function openPdf(path) {
  exitEditMode();
  $("#readerRendered").classList.add("hidden");
  $("#readerContent").classList.add("hidden");
  $("#readerFrontmatter").classList.add("hidden");
  $("#toggleRawButton").classList.add("hidden");
  $("#editButton").classList.add("hidden");
  state.editor = null;
  $("#readerPath").textContent = path;
  $("#readerTitle").textContent = path.split("/").pop();
  const frame = $("#readerPdf");
  frame.src = `/api/raw?path=${encodeURIComponent(path)}`;
  frame.classList.remove("hidden");
  $("#reader").showModal();
}
async function enterEditMode() {
  const editor = state.editor;
  if (!editor) return;
  $("#readerRendered").classList.add("hidden");
  $("#readerContent").classList.add("hidden");
  $("#readerFrontmatter").classList.add("hidden");
  $("#toggleRawButton").classList.add("hidden");
  $("#editButton").classList.add("hidden");
  if (editor.format === "notebook") {
    try {
      const data = await api(`/api/notebook?path=${encodeURIComponent(editor.path)}`);
      editor.mtime = data.mtime;
      $("#notebookEditor").innerHTML = data.cells.map((cell) => `
        <div class="nb-edit-cell" data-index="${cell.index}">
          <span class="nb-edit-badge ${cell.cell_type === "code" ? "code" : "md"}">${cell.cell_type === "code" ? "代码" : "Markdown"}</span>
          <textarea class="nb-edit-source" spellcheck="false" rows="${Math.max(2, String(cell.source).split("\n").length)}">${escapeHtml(cell.source)}</textarea>
        </div>`).join("");
      $("#notebookEditor").classList.remove("hidden");
    } catch (error) { toast(error.message); exitEditMode(); return; }
  } else {
    const raw = $("#readerContent").textContent;
    $("#editorArea").value = raw;
    $("#editorArea").classList.remove("hidden");
  }
  $("#editToolbar").classList.remove("hidden");
  state.editing = true;
}
function exitEditMode() {
  $("#editorArea").classList.add("hidden");
  $("#notebookEditor").classList.add("hidden");
  $("#notebookEditor").innerHTML = "";
  $("#editToolbar").classList.add("hidden");
  state.editing = false;
}
async function saveEdit() {
  const editor = state.editor;
  if (!editor) return;
  if (!await confirmAction("确认保存", "保存后会覆盖原文件，无法撤销。是否继续？")) return;
  const rebuild = $("#editRebuild").checked;
  const button = $("#saveButton");
  button.disabled = true; button.textContent = "保存中…";
  try {
    let data;
    if (editor.format === "notebook") {
      const cells = $$("#notebookEditor .nb-edit-cell").map((node) => ({
        index: Number(node.dataset.index),
        source: node.querySelector(".nb-edit-source").value,
      }));
      data = await api("/api/notebook/save", { method: "POST", body: JSON.stringify({
        path: editor.path, cells, confirmed: true, expected_mtime: editor.mtime, rebuild_indexes: rebuild,
      }) });
    } else {
      data = await api("/api/file/save", { method: "POST", body: JSON.stringify({
        path: editor.path, content: $("#editorArea").value, confirmed: true, expected_mtime: editor.mtime, rebuild_indexes: rebuild,
      }) });
    }
    toast(data.message || "已保存");
    exitEditMode();
    await openFile(editor.path);
    if (data.task) { await loadTasks(); openTaskDrawer(); }
    loadFileTree();
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; button.textContent = "保存"; }
}
function renderTree(node, depth = 0) {
  if (node.kind === "directory") return `<details class="tree-group"${depth === 0 ? " open" : ""}><summary title="${escapeHtml(node.path)}"><span class="tree-label">${escapeHtml(node.name)}</span></summary><div class="tree-children">${(node.children || []).map((child) => renderTree(child, depth + 1)).join("")}</div></details>`;
  const supported = ["md", "txt", "py", "js", "ts", "tsx", "jsx", "json", "yaml", "yml", "css", "html", "xml", "drawio", "csv", "ipynb", "pdf"].includes(node.kind);
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
    $("#inboxItems").classList.toggle("hidden", data.count === 0);
    $("#inboxEmpty").classList.toggle("hidden", data.count !== 0);
    $("#previewInboxButton").disabled = data.count === 0;
    $("#inboxItems").innerHTML = data.items.map((item) => `<div class="inbox-row"><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.kind.toUpperCase())} · ${formatBytes(item.size)}</span><time>${escapeHtml(item.updated.replace("T", " "))}</time></div>`).join("");
  } catch (error) { toast(error.message); }
}
async function previewInbox() {
  const button = $("#previewInboxButton");
  button.disabled = true; button.textContent = "生成中…";
  try {
    const data = await api("/api/inbox/preview", { method: "POST" });
    state.selectedPlanId = data.plan.id;
    setView("changes");
    await loadChanges(data.plan.id);
    toast("归档计划已生成，请检查 Diff");
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; button.textContent = "生成归档计划"; }
}

async function loadDirectories(defaultPath = null) {
  if (!state.directoriesLoaded) {
    const data = await api("/api/directories");
    $("#uploadDirectory").innerHTML = data.directories.map((item) => `<option value="${escapeHtml(item.path)}">${escapeHtml(item.label)}</option>`).join("");
    state.directoriesLoaded = true;
  }
  if (defaultPath && [...$("#uploadDirectory").options].some((option) => option.value === defaultPath)) $("#uploadDirectory").value = defaultPath;
}
async function openUpload(defaultPath = null) {
  try { await loadDirectories(defaultPath); $("#uploadDialog").showModal(); }
  catch (error) { toast(error.message); }
}
function setUploadFiles(files) {
  state.uploadFiles = [...files];
  $("#uploadFileList").classList.toggle("hidden", state.uploadFiles.length === 0);
  $("#uploadFileList").innerHTML = state.uploadFiles.map((file) => `<div class="upload-file-row"><strong>${escapeHtml(file.name)}</strong><span>${formatBytes(file.size)}</span></div>`).join("");
  resetUploadProgress();
}
function setUploadProgress(percent, text, phase) {
  const box = $("#uploadProgress");
  box.classList.remove("hidden", "success", "failed");
  if (phase) box.classList.add(phase);
  $("#uploadProgressFill").style.width = `${Math.max(0, Math.min(100, percent))}%`;
  $("#uploadProgressText").textContent = text;
}
function resetUploadProgress() {
  const box = $("#uploadProgress");
  box.classList.add("hidden");
  box.classList.remove("success", "failed");
  $("#uploadProgressFill").style.width = "0%";
  $("#uploadProgressText").textContent = "";
}
function uploadWithProgress(form, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/upload");
    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) onProgress(event.loaded / event.total);
    });
    xhr.addEventListener("load", () => {
      let data = {};
      try { data = JSON.parse(xhr.responseText); } catch (_) { /* 非 JSON 响应 */ }
      if (xhr.status >= 200 && xhr.status < 300) resolve(data);
      else reject(new Error(data.detail || `上传失败（HTTP ${xhr.status}）`));
    });
    xhr.addEventListener("error", () => reject(new Error("网络错误，未能连接到服务器")));
    xhr.addEventListener("abort", () => reject(new Error("上传已取消")));
    xhr.send(form);
  });
}
async function submitUpload(event) {
  event.preventDefault();
  if (!state.uploadFiles.length) { toast("请先选择文件"); return; }
  const button = $("#uploadSubmitButton");
  const form = new FormData();
  state.uploadFiles.forEach((file) => form.append("files", file));
  form.append("target_dir", $("#uploadDirectory").value);
  form.append("confirmed", "true");
  form.append("rebuild_indexes", $("#uploadIndexes").checked ? "true" : "false");
  const totalBytes = state.uploadFiles.reduce((sum, file) => sum + file.size, 0);
  button.disabled = true; button.textContent = "上传中…";
  setUploadProgress(0, "开始上传…", null);
  try {
    const data = await uploadWithProgress(form, (ratio) => {
      const percent = Math.round(ratio * 100);
      const sent = formatBytes(Math.round(ratio * totalBytes));
      setUploadProgress(percent, percent >= 100 ? "上传完成，服务器处理中…" : `正在上传 ${sent} / ${formatBytes(totalBytes)}（${percent}%）`, null);
    });
    setUploadProgress(100, `✓ ${data.message || "上传成功"}`, "success");
    toast(data.message || "上传成功");
    setUploadFiles([]); $("#uploadInput").value = "";
    await Promise.all([loadStatus(), loadInbox()]);
    if (data.task) { await loadTasks(); openTaskDrawer(); }
    state.directoriesLoaded = false;
    loadFileTree();
    setTimeout(() => { $("#uploadDialog").close(); resetUploadProgress(); }, 1200);
  } catch (error) {
    setUploadProgress(100, `✕ ${error.message}`, "failed");
    toast(error.message);
  }
  finally { button.disabled = false; button.textContent = "确认上传"; }
}

function planStatusLabel(status) { return status === "pending" ? "待审批" : status === "applied" ? "已应用" : status; }
async function loadChanges(selectId = null) {
  try {
    const data = await api("/api/changes");
    const pending = data.plans.filter((plan) => plan.status === "pending").length;
    $("#navChangeCount").textContent = pending;
    $("#changeList").innerHTML = data.plans.map((plan) => `<button class="change-item ${plan.id === (selectId || state.selectedPlanId) ? "active" : ""}" data-plan-id="${escapeHtml(plan.id)}"><header><strong>${escapeHtml(plan.title)}</strong><span class="status-pill ${escapeHtml(plan.status)}">${planStatusLabel(plan.status)}</span></header><p>${escapeHtml(plan.summary)}</p><time>${escapeHtml(plan.created_at.replace("T", " "))}</time></button>`).join("") || '<div class="empty">还没有变更计划。</div>';
    const selected = selectId || state.selectedPlanId;
    if (selected) await showPlan(selected);
  } catch (error) { toast(error.message); }
}
function renderDiffLine(line) {
  let className = "";
  if (line.startsWith("+") && !line.startsWith("+++")) className = "diff-line-add";
  else if (line.startsWith("-") && !line.startsWith("---")) className = "diff-line-remove";
  else if (line.startsWith("@@") || line.startsWith("MOVE") || line.startsWith("CREATE") || line.startsWith("  ->")) className = "diff-line-meta";
  return `<span class="${className}">${escapeHtml(line)}</span>`;
}
async function showPlan(planId) {
  try {
    const data = await api(`/api/changes/${encodeURIComponent(planId)}`);
    const plan = data.plan;
    state.selectedPlanId = plan.id;
    $$(".change-item").forEach((item) => item.classList.toggle("active", item.dataset.planId === plan.id));
    const diffs = plan.operations.map((operation) => `<div class="diff-operation">${String(operation.diff || `${operation.type} ${operation.target || ""}`).split("\n").map(renderDiffLine).join("\n")}</div>`).join("\n");
    const planActions = plan.status === "pending"
      ? `<div class="heading-actions"><button class="outline-button" id="rejectPlanButton">拒绝</button><button class="danger-button" id="applyPlanButton">批准并应用</button></div>`
      : `<span class="status-pill ${escapeHtml(plan.status)}">${planStatusLabel(plan.status)}</span>`;
    $("#diffPane").innerHTML = `<div class="diff-head"><div><h3>${escapeHtml(plan.title)}</h3><p>${escapeHtml(plan.summary)}</p></div>${planActions}</div><pre class="diff-content">${diffs || "无文本差异"}</pre>`;
    const apply = $("#applyPlanButton");
    if (apply) apply.addEventListener("click", () => applyPlan(plan));
    const reject = $("#rejectPlanButton");
    if (reject) reject.addEventListener("click", () => rejectPlan(plan));
  } catch (error) { toast(error.message); }
}
async function applyPlan(plan) {
  if (!await confirmAction("应用变更", `${plan.summary} 应用后会立即写入知识库，并后台更新检索索引。`)) return;
  try {
    const data = await api(`/api/changes/${encodeURIComponent(plan.id)}/apply`, { method: "POST", body: JSON.stringify({ confirmed: true }) });
    toast(data.message); await Promise.all([loadChanges(), loadStatus(), loadInbox()]);
    if (data.task) { await loadTasks(); openTaskDrawer(); }
  } catch (error) { toast(error.message); }
}

async function rejectPlan(plan) {
  if (!await confirmAction("拒绝变更", "该计划将标记为已拒绝，不会写入任何知识文件。")) return;
  try {
    const data = await api(`/api/changes/${encodeURIComponent(plan.id)}/reject`, { method: "POST", body: JSON.stringify({ confirmed: true }) });
    toast(data.message);
    await loadChanges();
    await showPlan(plan.id);
  } catch (error) { toast(error.message); }
}

function setAgentMode(mode) {
  state.agentMode = mode;
  $$(".mode-switch button").forEach((button) => button.classList.toggle("active", button.dataset.agentMode === mode));
  $("#outlineOptions").classList.toggle("hidden", mode !== "outline");
  $("#agentLabel").textContent = mode === "ask" ? "你想从知识库中了解什么？" : "围绕哪个主题生成结构？";
  $("#agentPrompt").placeholder = mode === "ask" ? "例如：我关于 RAG 的资料有哪些，还缺什么？" : "例如：RAG 工程实践";
  $("#agentWriteHint").textContent = mode === "ask" ? "使用混合检索并保留来源" : "先生成 Diff，审批后才写入输出区";
  $("#agentSubmit").textContent = mode === "ask" ? "开始检索" : "生成预览";
}
async function runAgent(event) {
  event.preventDefault();
  const prompt = $("#agentPrompt").value.trim();
  if (!prompt) return;
  const response = $("#agentResponse");
  response.innerHTML = '<span class="response-mark">✦</span><h3>正在整理本地知识…</h3><p>正在合并关键词与语义召回结果。</p>';
  try {
    if (state.agentMode === "ask") {
      const data = await api("/api/agent/ask", { method: "POST", body: JSON.stringify({ question: prompt, limit: 10 }) });
      response.innerHTML = `${data.warning ? `<div class="search-warning">${escapeHtml(data.warning)}</div>` : ""}<div class="markdown-body">${data.html}</div>`;
    } else {
      const kind = document.querySelector('input[name="outlineKind"]:checked').value;
      const data = await api("/api/agent/outline/preview", { method: "POST", body: JSON.stringify({ topic: prompt, kind, limit: 10 }) });
      state.selectedPlanId = data.plan.id; setView("changes"); await loadChanges(data.plan.id); toast("大纲 Diff 已生成，等待审批");
    }
  } catch (error) { response.innerHTML = `<span class="response-mark">!</span><h3>操作未完成</h3><p>${escapeHtml(error.message)}</p>`; }
}

function reportExcerpt(content) { return content.replace(/^---[\s\S]*?---/, "").replace(/^#.+$/m, "").replace(/[#`*_]/g, "").trim().slice(0, 120); }
async function loadReports() {
  try {
    const [status, reports, vector] = await Promise.all([api("/api/status"), api("/api/reports"), api("/api/vector/status")]);
    $("#healthIndexCount").textContent = `${status.indexed_count} 项`;
    $("#healthIndexTime").textContent = status.index_updated ? `更新于 ${status.index_updated.replace("T", " ")}` : "尚未建立索引";
    $("#vectorIndexCount").textContent = vector.indexed_chunks ? `${vector.indexed_chunks} chunks` : "未建立";
    $("#vectorIndexTime").textContent = vector.updated_at ? `${vector.dimension} 维 · ${vector.updated_at.replace("T", " ")}` : vector.model;
    $("#reportsGrid").innerHTML = reports.reports.map((report) => `<button class="report-item" data-path="${escapeHtml(report.path)}"><span>Report</span><h3>${escapeHtml(report.title)}</h3><p>${escapeHtml(reportExcerpt(report.content))}</p><time>${escapeHtml(report.updated.replace("T", " "))}</time></button>`).join("") || '<div class="empty">还没有健康报告。</div>';
  } catch (error) { toast(error.message); }
}
async function startMaintenance(endpoint, title, message) {
  if (!await confirmAction(title, message)) return;
  try {
    const data = await api(endpoint, { method: "POST", body: JSON.stringify({ confirmed: true }) });
    toast(data.message); await loadTasks(); openTaskDrawer();
  } catch (error) { toast(error.message); }
}

function taskStatusName(status) { return { queued: "排队中", running: "执行中", completed: "已完成", failed: "失败" }[status] || status; }
async function loadTasks() {
  try {
    const data = await api("/api/tasks");
    state.tasks = data.tasks;
    const active = data.tasks.filter((task) => ["queued", "running"].includes(task.status)).length;
    $("#activeTaskCount").textContent = active;
    $("#taskList").innerHTML = data.tasks.map((task) => `<article class="task-item ${escapeHtml(task.status)}"><header><h3>${escapeHtml(task.title)}</h3><span class="status-pill ${task.status === "completed" ? "applied" : ""}">${taskStatusName(task.status)}</span></header><p>${escapeHtml(task.error || task.message)}</p><div class="task-progress"><span style="width:${Number(task.progress) || 0}%"></span></div>${task.result ? `<div class="task-result">${escapeHtml(JSON.stringify(task.result))}</div>` : ""}<time>${escapeHtml(task.created_at.replace("T", " "))}</time></article>`).join("") || '<div class="empty">暂时没有后台任务。</div>';
    return active;
  } catch (error) { return 0; }
}
function openTaskDrawer() { $("#taskDrawer").classList.add("open"); $("#taskDrawer").setAttribute("aria-hidden", "false"); $("#drawerScrim").classList.add("open"); }
function closeTaskDrawer() { $("#taskDrawer").classList.remove("open"); $("#taskDrawer").setAttribute("aria-hidden", "true"); $("#drawerScrim").classList.remove("open"); }
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

$$(".nav-item").forEach((item) => item.addEventListener("click", () => setView(item.dataset.view)));
$("#menuButton").addEventListener("click", () => $(".sidebar").classList.toggle("open"));
$("#homeSearchForm").addEventListener("submit", (event) => { event.preventDefault(); runSearch($("#homeSearchInput").value); });
$("#searchForm").addEventListener("submit", (event) => { event.preventDefault(); runSearch($("#searchInput").value); });
$("#searchMode").addEventListener("click", (event) => { const button = event.target.closest("[data-mode]"); if (!button) return; state.searchMode = button.dataset.mode; $$("#searchMode button").forEach((item) => item.classList.toggle("active", item === button)); if ($("#searchInput").value.trim()) runSearch($("#searchInput").value); });
$(".search-hints").addEventListener("click", (event) => { const button = event.target.closest("[data-query]"); if (button) runSearch(button.dataset.query); });
document.addEventListener("click", (event) => { const file = event.target.closest("[data-path]"); if (file && !file.disabled) openFile(file.dataset.path); const plan = event.target.closest("[data-plan-id]"); if (plan && !event.target.closest("#applyPlanButton")) showPlan(plan.dataset.planId); });
$("#readerRendered").addEventListener("click", (event) => { const link = event.target.closest("a"); if (!link) return; const url = new URL(link.href, location.origin); if (url.pathname === "/api/wiki") { event.preventDefault(); openFile(url.searchParams.get("title"), "/api/wiki"); } });
$("#toggleRawButton").addEventListener("click", () => { $("#readerRendered").classList.toggle("hidden"); $("#readerContent").classList.toggle("hidden"); });
function closeReader() { exitEditMode(); $("#reader").close(); $("#readerPdf").removeAttribute("src"); }
$("#closeReader").addEventListener("click", closeReader);
$("#reader").addEventListener("click", (event) => { if (event.target === $("#reader") && !state.editing) closeReader(); });
$("#editButton").addEventListener("click", enterEditMode);
$("#saveButton").addEventListener("click", saveEdit);
$("#cancelEditButton").addEventListener("click", () => { exitEditMode(); if (state.editor) openFile(state.editor.path); });
$("#refreshLibraryButton").addEventListener("click", loadFileTree);
$("#previewInboxButton").addEventListener("click", previewInbox);
$("#refreshChangesButton").addEventListener("click", () => loadChanges());
$$(".mode-switch button").forEach((button) => button.addEventListener("click", () => setAgentMode(button.dataset.agentMode)));
$("#agentForm").addEventListener("submit", runAgent);

$("#openUploadButton").addEventListener("click", () => openUpload());
$("#inboxUploadButton").addEventListener("click", () => openUpload("00_Inbox"));
$("#closeUploadButton").addEventListener("click", () => { $("#uploadDialog").close(); resetUploadProgress(); });
$("#cancelUploadButton").addEventListener("click", () => { $("#uploadDialog").close(); resetUploadProgress(); });
$("#uploadInput").addEventListener("change", (event) => setUploadFiles(event.target.files));
$("#uploadDropzone").addEventListener("dragover", (event) => { event.preventDefault(); $("#uploadDropzone").classList.add("dragging"); });
$("#uploadDropzone").addEventListener("dragleave", () => $("#uploadDropzone").classList.remove("dragging"));
$("#uploadDropzone").addEventListener("drop", (event) => { event.preventDefault(); $("#uploadDropzone").classList.remove("dragging"); setUploadFiles(event.dataTransfer.files); });
$("#uploadForm").addEventListener("submit", submitUpload);

$("#taskCenterButton").addEventListener("click", async () => { await loadTasks(); openTaskDrawer(); });
$("#closeTaskDrawer").addEventListener("click", closeTaskDrawer);
$("#drawerScrim").addEventListener("click", closeTaskDrawer);
$("#rebuildIndexButton").addEventListener("click", () => startMaintenance("/api/maintenance/rebuild-indexes", "重建全部索引", "将重建 FTS5 关键词索引，并把文档切片发送到局域网 Qwen Embedding 服务生成 2048 维向量。"));
$("#runHealthButton").addEventListener("click", () => startMaintenance("/api/maintenance/health", "运行完整体检", "将更新体检报告、双链建议、关键词索引和向量索引。"));

Promise.all([loadStatus(), loadChanges(), loadTasks()]).catch((error) => toast(error.message));
setInterval(async () => { const active = await loadTasks(); if (!active && !$("#taskDrawer").classList.contains("open")) return; if (!active) { loadStatus(); if (state.currentView === "health") loadReports(); } }, 1800);
