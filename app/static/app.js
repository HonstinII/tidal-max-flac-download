const state = {
  setup: null,
  authSession: null,
  eventSource: null,
  installEventSource: null,
  language: localStorage.getItem("language") || "en",
  lastOutputDir: null,
  toastTimer: null,
  authStatus: "",
};

const els = {
  langEn: document.querySelector("#langEn"),
  langZh: document.querySelector("#langZh"),
  accountControl: document.querySelector("#accountControl"),
  accountDropdown: document.querySelector("#accountDropdown"),
  unbindButton: document.querySelector("#unbindButton"),
  workspaceAccountButton: document.querySelector("#workspaceAccountButton"),
  setupPanel: document.querySelector("#setupPanel"),
  workspace: document.querySelector("#workspace"),
  checks: document.querySelector("#checks"),
  platformInfo: document.querySelector("#platformInfo"),
  installToolsButton: document.querySelector("#installToolsButton"),
  bundledFlacButton: document.querySelector("#bundledFlacButton"),
  recheckButton: document.querySelector("#recheckButton"),
  installLog: document.querySelector("#installLog"),
  bindButton: document.querySelector("#bindButton"),
  bindMessage: document.querySelector("#bindMessage"),
  urlInput: document.querySelector("#urlInput"),
  outputDir: document.querySelector("#outputDir"),
  pickFolder: document.querySelector("#pickFolder"),
  openFolder: document.querySelector("#openFolder"),
  concurrency: document.querySelector("#concurrency"),
  embedCovers: document.querySelector("#embedCovers"),
  embedLyrics: document.querySelector("#embedLyrics"),
  skipExisting: document.querySelector("#skipExisting"),
  downloadButton: document.querySelector("#downloadButton"),
  events: document.querySelector("#events"),
  jobStatus: document.querySelector("#jobStatus"),
  toast: document.querySelector("#toast"),
};

const copy = {
  en: {
    ready: "Ready",
    missing: "Missing",
    checkingBinding: "Checking binding...",
    bound: "Bound to Tidal",
    notBound: "Tidal not bound",
    unbind: "Unbind",
    unbindAccount: "Unbind account",
    unbindConfirm: "Unbind this Tidal account? You can bind a different account afterward.",
    core: "Core",
    optional: "Optional",
    step1: "Step 1",
    step2: "Step 2",
    checkChain: "Check the chain",
    checkChainCopy: "Core tools must be ready before the downloader opens. Optional tools only affect cover or metadata extras.",
    bindTidal: "Bind Tidal",
    bindTidalCopy: "Open Tidal's official authorization page. You sign in there; this app never sees your password.",
    startBinding: "Start Tidal binding",
    accountSettings: "Account",
    checkStreamrip: "Core download tool that manages Tidal-compatible download configuration.",
    checkFfmpeg: "Core audio processor used to assemble and write FLAC files.",
    checkMetaflac: "Optional metadata helper for embedding cover art into FLAC files.",
    checkConfig: "Core local config file used to store Tidal authorization safely.",
    installMissing: "Install missing tools",
    useBundledFlac: "Use bundled FLAC tools",
    recheck: "Recheck",
    platform: "Platform",
    copyCommand: "Copy command",
    commandCopied: "Command copied.",
    bundledFlacReady: "Bundled FLAC tools extracted. Rechecking environment...",
    bundledFlacMissing: "Bundled FLAC tools are not included in this build.",
    installingTools: "Installing missing tools...",
    installComplete: "Tool installation complete. Rechecking environment...",
    installFailed: "Tool installation failed.",
    notFound: "not found",
    download: "Download",
    pasteUrls: "Paste Tidal URLs",
    outputFolder: "Output folder",
    choose: "Choose",
    openFolder: "Open folder",
    segmentConcurrency: "Segment concurrency",
    embedCover: "Embed cover art",
    embedLyrics: "Embed lyrics",
    skipExisting: "Skip existing files",
    startDownload: "Start download",
    queue: "Queue",
    sessionEvents: "Session events",
    idle: "Idle",
    creatingLink: "Creating Tidal authorization link...",
    opened: "Opened",
    status: "Status",
    bindingWait: "Binding Tidal. Please do not refresh this page.",
    bindingPending: "Waiting for Tidal authorization. Keep this page open.",
    bindingSuccess: "Tidal bound. Opening the downloader...",
    bindingFailed: "Tidal binding failed. Please start again.",
    bindingExpired: "Tidal binding expired. Please start again.",
    authLinkHelp: "Click to open authorization page",
    pasteAtLeastOne: "Paste at least one Tidal URL.",
    fetching: "Fetching",
    fetched: "Fetch succeeded",
    downloading: "Downloading",
    complete: "Download complete",
    failed: "Download failed",
    tracks: "track(s)",
  },
  zh: {
    ready: "就绪",
    missing: "缺失",
    checkingBinding: "正在检查绑定...",
    bound: "已绑定 Tidal",
    notBound: "Tidal 未绑定",
    unbind: "解绑",
    unbindAccount: "解绑账号",
    unbindConfirm: "要解绑当前 Tidal 账号吗？之后可以重新绑定其他账号。",
    core: "核心",
    optional: "可选",
    step1: "步骤 1",
    step2: "步骤 2",
    checkChain: "检查环境",
    checkChainCopy: "核心工具就绪后才能进入下载台；可选工具只影响封面或元数据增强。",
    bindTidal: "绑定 Tidal",
    bindTidalCopy: "打开 Tidal 官方授权页。你在那里登录，本应用不会看到你的密码。",
    startBinding: "开始绑定 Tidal",
    accountSettings: "账号",
    checkStreamrip: "核心下载工具，用来管理兼容 Tidal 的下载配置。",
    checkFfmpeg: "核心音频处理工具，用来合并音频并写出 FLAC 文件。",
    checkMetaflac: "可选元数据工具，用来把封面嵌入 FLAC 文件。",
    checkConfig: "核心本地配置文件，用来安全保存 Tidal 授权。",
    installMissing: "安装缺失工具",
    useBundledFlac: "使用内置 FLAC 工具",
    recheck: "重新检查",
    platform: "平台",
    copyCommand: "复制命令",
    commandCopied: "命令已复制。",
    bundledFlacReady: "内置 FLAC 工具已解压，正在重新检查环境...",
    bundledFlacMissing: "当前构建未包含内置 FLAC 工具包。",
    installingTools: "正在安装缺失工具...",
    installComplete: "工具安装完成，正在重新检查环境...",
    installFailed: "工具安装失败。",
    notFound: "未找到",
    download: "下载",
    pasteUrls: "粘贴 Tidal 链接",
    outputFolder: "输出目录",
    choose: "选择",
    openFolder: "打开文件夹",
    segmentConcurrency: "分段并发",
    embedCover: "嵌入封面",
    embedLyrics: "嵌入歌词",
    skipExisting: "跳过已有文件",
    startDownload: "开始下载",
    queue: "队列",
    sessionEvents: "会话事件",
    idle: "空闲",
    creatingLink: "正在创建 Tidal 授权链接...",
    opened: "已打开",
    status: "状态",
    bindingWait: "正在绑定 Tidal，请勿刷新页面。",
    bindingPending: "等待 Tidal 授权中，请保持本页面打开。",
    bindingSuccess: "Tidal 绑定成功，正在进入工作台...",
    bindingFailed: "Tidal 绑定失败，请重新开始。",
    bindingExpired: "Tidal 绑定已过期，请重新开始。",
    authLinkHelp: "点击进入授权页面",
    pasteAtLeastOne: "请至少粘贴一个 Tidal 链接。",
    fetching: "抓取中",
    fetched: "抓取成功",
    downloading: "下载中",
    complete: "下载完成",
    failed: "下载失败",
    tracks: "首曲目",
  },
};

function t(key) {
  return copy[state.language][key] || copy.en[key] || key;
}

function showToast(message, tone = "info", autoHideMs = 0) {
  els.toast.textContent = message;
  els.toast.className = `toast ${tone}`;
  if (state.toastTimer) clearTimeout(state.toastTimer);
  if (autoHideMs > 0) {
    state.toastTimer = setTimeout(() => {
      els.toast.classList.add("hidden");
    }, autoHideMs);
  }
}

function applyLanguage() {
  document.documentElement.lang = state.language === "zh" ? "zh-CN" : "en";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  els.langEn.classList.toggle("active", state.language === "en");
  els.langZh.classList.toggle("active", state.language === "zh");
  if (state.setup) {
    renderChecks();
    renderMode();
  }
}

function checkRow({ label, ok, detail, description, required, path }) {
  const stateClass = ok ? "ok" : required ? "bad" : "warn";
  const stateText = ok ? t("ready") : t("missing");
  const requirement = required ? t("core") : t("optional");
  const toolPath = path ? `<small>${path}</small>` : "";
  return `
    <div class="check ${required ? "required" : "optional"}">
      <div class="check-head">
        <strong>${label}</strong>
        <span class="check-pill">${requirement}</span>
      </div>
      <p>${description}</p>
      <span class="${stateClass}">${stateText}</span> ${detail || ""}
      ${toolPath}
    </div>
  `;
}

function hasCoreSetup() {
  return Boolean(
    state.setup?.tools?.streamrip &&
      state.setup?.tools?.ffmpeg &&
      state.setup?.streamrip_config?.exists,
  );
}

function missingInstallableTools() {
  if (!state.setup) return [];
  return ["streamrip", "ffmpeg", "metaflac"].filter((tool) => !state.setup.tools?.[tool]);
}

function showBundledFlacOption() {
  return Boolean(
    state.setup?.platform?.system === "Windows" &&
      state.setup?.tools?.metaflac === false,
  );
}

async function refreshSetup() {
  const response = await fetch("/api/setup/status");
  state.setup = await response.json();
  els.outputDir.value = state.setup.output_dir;
  renderChecks();
  renderMode();
}

function renderChecks() {
  const platform = state.setup.platform?.name || state.setup.platform?.system || "";
  els.platformInfo.textContent = platform ? `${t("platform")}: ${platform}` : "";
  const details = state.setup.tools_detail || {};
  els.checks.innerHTML = [
    checkRow({
      label: "streamrip",
      ok: state.setup.tools.streamrip,
      detail: state.setup.tools.streamrip ? "" : t("notFound"),
      description: details.streamrip?.description || t("checkStreamrip"),
      required: true,
      path: details.streamrip?.path,
    }),
    checkRow({
      label: "ffmpeg",
      ok: state.setup.tools.ffmpeg,
      detail: state.setup.tools.ffmpeg ? "" : t("notFound"),
      description: details.ffmpeg?.description || t("checkFfmpeg"),
      required: true,
      path: details.ffmpeg?.path,
    }),
    checkRow({
      label: "metaflac",
      ok: state.setup.tools.metaflac,
      detail: state.setup.tools.metaflac ? "" : t("notFound"),
      description: details.metaflac?.description || t("checkMetaflac"),
      required: false,
      path: details.metaflac?.path,
    }),
    checkRow({
      label: "streamrip config",
      ok: state.setup.streamrip_config.exists,
      detail: state.setup.streamrip_config.path,
      description: t("checkConfig"),
      required: true,
    }),
  ].join("");
  els.installToolsButton.classList.toggle("hidden", missingInstallableTools().length === 0);
  els.bundledFlacButton.classList.toggle("hidden", !showBundledFlacOption());
}

function renderMode() {
  const bound = Boolean(state.setup?.tidal?.bound);
  const coreReady = hasCoreSetup();
  const canOpenWorkspace = bound && coreReady;
  els.setupPanel.classList.toggle("hidden", canOpenWorkspace);
  els.workspace.classList.toggle("hidden", !canOpenWorkspace);
  els.accountControl.classList.toggle("hidden", !bound);
  if (bound) {
    els.workspaceAccountButton.textContent = `${t("bound")} (${state.setup.tidal.country_code})`;
  } else if (!state.authSession) {
    els.workspaceAccountButton.textContent = t("accountSettings");
  }
  closeAccountMenu();
}

async function startBinding() {
  els.bindButton.disabled = true;
  els.bindMessage.textContent = t("creatingLink");
  showToast(t("bindingWait"), "info");
  try {
    const response = await fetch("/api/auth/tidal/start", { method: "POST" });
    state.authSession = await response.json();
    state.authStatus = t("bindingWait");
    renderAuthMessage();
    window.open(state.authSession.url, "_blank", "noopener,noreferrer");
    pollBinding();
  } catch (error) {
    els.bindButton.disabled = false;
    els.bindMessage.textContent = error.message;
    showToast(t("bindingFailed"), "error", 5000);
  }
}

function renderAuthMessage() {
  if (!state.authSession?.url) {
    els.bindMessage.textContent = state.authStatus || "";
    return;
  }
  els.bindMessage.innerHTML = `
    <a href="${state.authSession.url}" target="_blank" rel="noreferrer">${t("authLinkHelp")}</a>
    <span>${state.authStatus}</span>
  `;
}

async function pollBinding() {
  if (!state.authSession) return;
  let data;
  try {
    const response = await fetch(`/api/auth/tidal/status/${state.authSession.session_id}`);
    data = await response.json();
  } catch (error) {
    els.bindButton.disabled = false;
    els.bindMessage.textContent = error.message;
    showToast(t("bindingFailed"), "error", 5000);
    return;
  }
  state.authStatus = `${t("status")}: ${data.status}`;
  renderAuthMessage();
  if (data.status === "success") {
    showToast(t("bindingSuccess"), "success", 2400);
    await refreshSetup();
    els.bindButton.disabled = false;
    return;
  }
  if (data.status === "pending") {
    state.authStatus = t("bindingPending");
    renderAuthMessage();
    showToast(t("bindingPending"), "info");
  }
  if (data.status === "expired") {
    state.authStatus = t("bindingExpired");
    renderAuthMessage();
    showToast(t("bindingExpired"), "error", 5000);
    els.bindButton.disabled = false;
    return;
  }
  if (data.status === "error" || data.status === "missing") {
    state.authStatus = data.message || t("bindingFailed");
    renderAuthMessage();
    showToast(data.message || t("bindingFailed"), "error", 5000);
    els.bindButton.disabled = false;
    return;
  }
  setTimeout(pollBinding, 3000);
}

function addEvent(event) {
  const display = toDisplayEvent(event);
  if (!display) return;
  const row = document.createElement("div");
  row.className = "event";
  const title = display.title ? ` ${display.title}` : "";
  row.innerHTML = `<strong>${display.label}</strong>${title}<br>${display.detail || ""}`;
  els.events.prepend(row);
}

function toDisplayEvent(event) {
  if (event.stage === "fetching" || event.stage === "resolving") {
    return { label: t("fetching"), detail: event.url };
  }
  if (event.stage === "fetched") {
    return { label: t("fetched"), detail: `${event.count || 0} ${t("tracks")}` };
  }
  if (event.stage === "downloading") {
    return {
      label: t("downloading"),
      title: `${event.artist || ""} - ${event.title || event.track_id || ""}`.trim(),
    };
  }
  if (event.stage === "downloaded" || event.stage === "skipped") {
    return {
      label: t("complete"),
      title: `${event.artist || ""} - ${event.title || event.track_id || ""}`.trim(),
      detail: event.path,
    };
  }
  if (event.stage === "error" || event.stage === "failed") {
    return { label: t("failed"), detail: event.message || event.url };
  }
  return null;
}

async function startDownload() {
  const urls = els.urlInput.value
    .split(/\s+/)
    .map((url) => url.trim())
    .filter(Boolean);
  if (!urls.length) {
    addEvent({ stage: "error", message: t("pasteAtLeastOne") });
    return;
  }
  els.downloadButton.disabled = true;
  els.openFolder.classList.add("hidden");
  els.events.innerHTML = "";
  const response = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      urls,
      output_dir: els.outputDir.value,
      concurrency: Number(els.concurrency.value || 10),
      embed_covers: els.embedCovers.checked,
      embed_lyrics: els.embedLyrics.checked,
      skip_existing: els.skipExisting.checked,
    }),
  });
  const job = await response.json();
  els.jobStatus.textContent = `Job ${job.job_id.slice(0, 8)}`;
  state.lastOutputDir = els.outputDir.value;
  if (state.eventSource) state.eventSource.close();
  state.eventSource = new EventSource(`/api/jobs/${job.job_id}/events`);
  state.eventSource.onmessage = (message) => {
    const event = JSON.parse(message.data);
    addEvent(event);
    if (event.stage === "complete" || event.stage === "failed") {
      els.downloadButton.disabled = false;
      if (event.stage === "complete") {
        els.openFolder.classList.remove("hidden");
      }
      state.eventSource.close();
    }
  };
}

function addInstallLog(line, command = "") {
  els.installLog.classList.remove("hidden");
  const row = document.createElement("div");
  row.className = "install-row";
  row.textContent = line;
  if (command) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-command";
    button.textContent = t("copyCommand");
    button.addEventListener("click", async () => {
      await navigator.clipboard.writeText(command);
      showToast(t("commandCopied"), "success", 1600);
    });
    row.append(button);
  }
  els.installLog.append(row);
  els.installLog.scrollTop = els.installLog.scrollHeight;
}

async function installMissingTools() {
  els.installToolsButton.disabled = true;
  els.installLog.innerHTML = "";
  addInstallLog(t("installingTools"));
  showToast(t("installingTools"), "info");
  const response = await fetch("/api/tools/install", { method: "POST" });
  const job = await response.json();
  if (state.installEventSource) state.installEventSource.close();
  state.installEventSource = new EventSource(`/api/tools/install/${job.job_id}/events`);
  state.installEventSource.onmessage = async (message) => {
    const event = JSON.parse(message.data);
    addInstallLog(event.message || event.label || event.stage, event.copy_command || "");
    if (event.stage === "complete") {
      state.installEventSource.close();
      els.installToolsButton.disabled = false;
      showToast(t("installComplete"), "success", 3500);
      await refreshSetup();
    }
    if (event.stage === "failed") {
      state.installEventSource.close();
      els.installToolsButton.disabled = false;
      showToast(event.message || t("installFailed"), "error", 5000);
      await refreshSetup();
    }
  };
}

async function useBundledFlac() {
  els.bundledFlacButton.disabled = true;
  const response = await fetch("/api/tools/bundled-flac", { method: "POST" });
  const result = await response.json();
  if (result.ok) {
    showToast(t("bundledFlacReady"), "success", 2500);
  } else {
    showToast(result.message || t("bundledFlacMissing"), "error", 5000);
    addInstallLog(result.message || t("bundledFlacMissing"));
  }
  els.bundledFlacButton.disabled = false;
  await refreshSetup();
}

async function unbindTidal() {
  if (!confirm(t("unbindConfirm"))) return;
  closeAccountMenu();
  await fetch("/api/auth/tidal/unbind", { method: "POST" });
  els.events.innerHTML = "";
  els.openFolder.classList.add("hidden");
  await refreshSetup();
}

function closeAccountMenu() {
  els.accountDropdown.classList.add("hidden");
  els.workspaceAccountButton.setAttribute("aria-expanded", "false");
}

function toggleAccountMenu() {
  if (!state.setup?.tidal?.bound) return;
  const isOpen = !els.accountDropdown.classList.contains("hidden");
  els.accountDropdown.classList.toggle("hidden", isOpen);
  els.workspaceAccountButton.setAttribute("aria-expanded", String(!isOpen));
}

els.bindButton.addEventListener("click", startBinding);
els.downloadButton.addEventListener("click", startDownload);
els.installToolsButton.addEventListener("click", installMissingTools);
els.bundledFlacButton.addEventListener("click", useBundledFlac);
els.recheckButton.addEventListener("click", refreshSetup);
els.workspaceAccountButton.addEventListener("click", toggleAccountMenu);
els.unbindButton.addEventListener("click", unbindTidal);
document.addEventListener("click", (event) => {
  if (!els.workspaceAccountButton.contains(event.target) && !els.accountDropdown.contains(event.target)) {
    closeAccountMenu();
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeAccountMenu();
});
els.langEn.addEventListener("click", () => {
  state.language = "en";
  localStorage.setItem("language", state.language);
  applyLanguage();
});
els.langZh.addEventListener("click", () => {
  state.language = "zh";
  localStorage.setItem("language", state.language);
  applyLanguage();
});
els.pickFolder.addEventListener("click", async () => {
  const response = await fetch("/api/folders/pick", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: els.outputDir.value }),
  });
  const data = await response.json();
  if (data.path) els.outputDir.value = data.path;
});
els.openFolder.addEventListener("click", async () => {
  await fetch("/api/folders/open", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: els.outputDir.value }),
  });
});
refreshSetup().catch((error) => {
  els.bindMessage.textContent = `Startup failed: ${error.message}`;
});
applyLanguage();
