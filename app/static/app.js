const state = {
  setup: null,
  authSession: null,
  eventSource: null,
  installEventSource: null,
  language: localStorage.getItem("language") || "en",
  lastOutputDir: null,
  toastTimer: null,
  authStatus: "",
  activeRunId: null,
  previewTimer: null,
  previewAbort: null,
  audioQuality: localStorage.getItem("audioQuality") || "max",
  clearedQueueBefore: 0,
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
  recheckButton: document.querySelector("#recheckButton"),
  installLog: document.querySelector("#installLog"),
  bindButton: document.querySelector("#bindButton"),
  bindMessage: document.querySelector("#bindMessage"),
  urlInput: document.querySelector("#urlInput"),
  outputDir: document.querySelector("#outputDir"),
  pickFolder: document.querySelector("#pickFolder"),
  openFolder: document.querySelector("#openFolder"),
  pauseRun: document.querySelector("#pauseRun"),
  resumeRun: document.querySelector("#resumeRun"),
  cancelRun: document.querySelector("#cancelRun"),
  clearQueue: document.querySelector("#clearQueue"),
  exportLog: document.querySelector("#exportLog"),
  concurrency: document.querySelector("#concurrency"),
  embedCovers: document.querySelector("#embedCovers"),
  embedLyrics: document.querySelector("#embedLyrics"),
  audioQualityLabel: document.querySelector("#audioQualityLabel"),
  audioQualityButton: document.querySelector("#audioQualityButton"),
  audioQualityMenu: document.querySelector("#audioQualityMenu"),
  lyricsMode: document.querySelector("#lyricsMode"),
  writeLrc: document.querySelector("#writeLrc"),
  albumTemplate: document.querySelector("#albumTemplate"),
  filenameTemplate: document.querySelector("#filenameTemplate"),
  singleFilenameTemplate: document.querySelector("#singleFilenameTemplate"),
  existingStrategy: document.querySelector("#existingStrategy"),
  settingsButton: document.querySelector("#settingsButton"),
  settingsModal: document.querySelector("#settingsModal"),
  closeSettingsButton: document.querySelector("#closeSettingsButton"),
  previewResults: document.querySelector("#previewResults"),
  downloadButton: document.querySelector("#downloadButton"),
  queueTable: document.querySelector("#queueTable"),
  events: document.querySelector("#events"),
  jobStatus: document.querySelector("#jobStatus"),
  coverToolModal: document.querySelector("#coverToolModal"),
  installCoverToolButton: document.querySelector("#installCoverToolButton"),
  recheckCoverToolButton: document.querySelector("#recheckCoverToolButton"),
  cancelCoverToolButton: document.querySelector("#cancelCoverToolButton"),
  toast: document.querySelector("#toast"),
};

const copy = {
  en: {
    ready: "Ready",
    missing: "Missing",
    bindingRequired: "Tidal binding required",
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
    checkChainCopy: "Core tools must be ready before the downloader opens. Cover embedding is checked only when you enable it.",
    bindTidal: "Bind Tidal",
    bindTidalCopy: "Open Tidal's official authorization page. You sign in there; this app never sees your password.",
    startBinding: "Start Tidal binding",
    accountSettings: "Account",
    checkStreamrip: "Core download tool that manages Tidal-compatible download configuration.",
    checkFfmpeg: "Core audio processor used to assemble and write FLAC files.",
    checkMetaflac: "Optional metadata helper for embedding cover art into FLAC files.",
    checkConfig: "Tidal authorization file. It is created after you bind Tidal; this is not a tool install.",
    installMissing: "Install missing tools",
    useBundledFlac: "Use bundled FLAC tools",
    optionalCoverTool: "Optional cover tool",
    coverToolMissingTitle: "Cover embedding needs metaflac",
    coverToolMissingCopy: "Downloads can continue without this tool, but cover art cannot be embedded into FLAC files.",
    coverToolManualCopy: "If automatic setup fails, download the Windows FLAC tools from the official page, install or unzip them, then recheck.",
    officialSource: "Official source",
    installCoverTool: "Install cover tool",
    manualDownload: "Manual download",
    cancelCoverTool: "Cancel",
    coverToolInstalling: "Installing cover embedding tool...",
    coverToolInstalled: "Cover tool is ready. Cover embedding is enabled.",
    recheck: "Recheck",
    platform: "Platform",
    copyCommand: "Copy command",
    officialDownload: "Official download",
    commandCopied: "Command copied.",
    bundledFlacReady: "Bundled FLAC tools extracted. Rechecking environment...",
    bundledFlacMissing: "Bundled FLAC tools are not included in this build.",
    installingTools: "Installing missing tools...",
    installComplete: "Tool installation complete. Rechecking environment...",
    installFailed: "Tool installation failed.",
    toolsReady: "Core tools are ready.",
    notFound: "not found",
    download: "Download",
    pasteUrls: "Paste Tidal URLs",
    outputFolder: "Output folder",
    choose: "Choose",
    openFolder: "Open folder",
    segmentConcurrency: "Segment concurrency",
    concurrencyHelp: "Controls how many audio segments download at the same time. Higher values can speed up fast networks, but may increase CPU, memory, disk activity, and the chance of network throttling or unstable downloads.",
    embedCover: "Embed cover art",
    embedLyrics: "Embed lyrics",
    qualityAccountNote: "Maximum quality depends on the bound Tidal account.",
    qualityMax: "Max",
    qualityMaxDetail: "Up to 24-bit, 192 kHz",
    qualityHigh: "High",
    qualityHighDetail: "16-bit, 44.1 kHz",
    lyricsMode: "Lyrics mode",
    lyricsAuto: "Auto",
    lyricsAutoDetail: "Use synced lyrics when Tidal provides them.",
    lyricsSynced: "Synced",
    lyricsSyncedDetail: "Prefer timestamped lyrics for compatible players.",
    lyricsPlain: "Plain",
    lyricsPlainDetail: "Write regular text lyrics without timing.",
    writeLrc: "Write .lrc file",
    downloadSettings: "Download settings",
    metadataSettings: "Metadata and files",
    done: "Done",
    albumTemplate: "Album folder template",
    filenameTemplate: "Album file template",
    singleFilenameTemplate: "Single file template",
    existingStrategy: "Existing files",
    strategySkip: "Skip",
    strategySkipDetail: "Keep existing files and skip duplicates.",
    strategyOverwrite: "Overwrite",
    strategyOverwriteDetail: "Replace files with the new download.",
    strategyKeepBoth: "Keep both",
    strategyKeepBothDetail: "Save a new copy when a file exists.",
    lossyConfirm: "Due to Tidal's official restrictions, this song's HIGH format can only be downloaded as AAC. Continue?",
    lossyAvailableDetail: "Tidal only exposed an AAC stream for this track/account at High quality. Continue with AAC to download an .m4a file.",
    existingFileSkipped: "This folder already has this song. Choose another output folder or change the download setting.",
    openFileLocation: "Open file location",
    previewParsing: "Parsing preview...",
    previewFailed: "Parse failed. Please paste a complete Tidal link.",
    startDownload: "Start download",
    queue: "Queue",
    sessionEvents: "Queue status",
    pauseRun: "Pause",
    resumeRun: "Resume",
    cancelRun: "Cancel",
    clearQueue: "Clear",
    exportLog: "Export log",
    retry: "Retry",
    previewEmpty: "Preview is empty.",
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
    bindingRequired: "需要绑定 Tidal",
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
    checkChainCopy: "核心工具就绪后才能进入下载台；封面嵌入只在你启用时检查。",
    bindTidal: "绑定 Tidal",
    bindTidalCopy: "打开 Tidal 官方授权页。你在那里登录，本应用不会看到你的密码。",
    startBinding: "开始绑定 Tidal",
    accountSettings: "账号",
    checkStreamrip: "核心下载工具，用来管理兼容 Tidal 的下载配置。",
    checkFfmpeg: "核心音频处理工具，用来合并音频并写出 FLAC 文件。",
    checkMetaflac: "可选元数据工具，用来把封面嵌入 FLAC 文件。",
    checkConfig: "Tidal 授权文件。绑定 Tidal 后会自动生成，这不是工具安装项。",
    installMissing: "安装缺失工具",
    useBundledFlac: "使用内置 FLAC 工具",
    optionalCoverTool: "可选封面工具",
    coverToolMissingTitle: "嵌入封面需要 metaflac",
    coverToolMissingCopy: "没有这个工具也可以继续下载，但无法把封面写入 FLAC 文件。",
    coverToolManualCopy: "如果自动安装失败，请从官方页面下载 Windows FLAC 工具，安装或解压后再重新检查。",
    officialSource: "官方来源",
    installCoverTool: "安装封面工具",
    manualDownload: "手动下载",
    cancelCoverTool: "取消",
    coverToolInstalling: "正在安装封面嵌入工具...",
    coverToolInstalled: "封面工具已就绪，已启用嵌入封面。",
    recheck: "重新检查",
    platform: "平台",
    copyCommand: "复制命令",
    officialDownload: "官方下载",
    commandCopied: "命令已复制。",
    bundledFlacReady: "内置 FLAC 工具已解压，正在重新检查环境...",
    bundledFlacMissing: "当前构建未包含内置 FLAC 工具包。",
    installingTools: "正在安装缺失工具...",
    installComplete: "工具安装完成，正在重新检查环境...",
    installFailed: "工具安装失败。",
    toolsReady: "核心工具已就绪。",
    notFound: "未找到",
    download: "下载",
    pasteUrls: "粘贴 Tidal 链接",
    outputFolder: "输出目录",
    choose: "选择",
    openFolder: "打开文件夹",
    segmentConcurrency: "分段并发",
    concurrencyHelp: "控制同时下载多少个音频分段。数值越大，在网络足够快时可能更快，但也会增加 CPU、内存、磁盘占用，并提高被网络限速或下载不稳定的概率。",
    embedCover: "嵌入封面",
    embedLyrics: "嵌入歌词",
    qualityAccountNote: "最高下载品质由当前绑定的 Tidal 账号决定。",
    qualityMax: "Max",
    qualityMaxDetail: "最高 24-bit, 192 kHz",
    qualityHigh: "High",
    qualityHighDetail: "16-bit, 44.1 kHz",
    lyricsMode: "歌词模式",
    lyricsAuto: "自动",
    lyricsAutoDetail: "Tidal 提供同步歌词时优先使用。",
    lyricsSynced: "同步歌词",
    lyricsSyncedDetail: "优先写入带时间戳的歌词。",
    lyricsPlain: "普通歌词",
    lyricsPlainDetail: "写入不带时间戳的文本歌词。",
    writeLrc: "写出 .lrc 文件",
    downloadSettings: "下载设置",
    metadataSettings: "元数据与文件",
    done: "完成",
    albumTemplate: "专辑目录模板",
    filenameTemplate: "专辑文件名模板",
    singleFilenameTemplate: "单曲文件名模板",
    existingStrategy: "已有文件",
    strategySkip: "跳过",
    strategySkipDetail: "保留已有文件，跳过重复歌曲。",
    strategyOverwrite: "覆盖",
    strategyOverwriteDetail: "用本次下载替换已有文件。",
    strategyKeepBoth: "保留两个",
    strategyKeepBothDetail: "已有文件时另存一个新副本。",
    lossyConfirm: "受 Tidal 官方限制，此歌曲 HIGH格式 只能以 AAC 格式下载，是否继续？",
    lossyAvailableDetail: "当前歌曲/账号在 High 品质下只返回 AAC 流。继续后会下载 .m4a 文件。",
    existingFileSkipped: "该目录已存在该歌曲，请选择其他目录下载或更改下载设置。",
    openFileLocation: "打开文件位置",
    previewParsing: "解析中...",
    previewFailed: "解析失败，请放入完整的tidal的链接",
    startDownload: "开始下载",
    queue: "队列",
    sessionEvents: "队列状态",
    pauseRun: "暂停",
    resumeRun: "继续",
    cancelRun: "取消",
    clearQueue: "清空",
    exportLog: "导出日志",
    retry: "重试",
    previewEmpty: "没有预览内容。",
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
  document.querySelectorAll("[data-i18n-title]").forEach((node) => {
    const value = t(node.dataset.i18nTitle);
    node.setAttribute("title", value);
    node.setAttribute("aria-label", value);
  });
  document.querySelectorAll("[data-tooltip-key]").forEach((node) => {
    node.dataset.tooltip = t(node.dataset.tooltipKey);
  });
  els.langEn.classList.toggle("active", state.language === "en");
  els.langZh.classList.toggle("active", state.language === "zh");
  if (els.audioQualityButton) {
    els.audioQualityLabel.textContent = t(state.audioQuality === "high" ? "qualityHigh" : "qualityMax");
  }
  syncCustomSelects();
  if (state.setup) {
    renderChecks();
    renderMode();
  }
}

function setAudioQuality(value) {
  state.audioQuality = value === "high" ? "high" : "max";
  localStorage.setItem("audioQuality", state.audioQuality);
  els.audioQualityLabel.textContent = t(state.audioQuality === "high" ? "qualityHigh" : "qualityMax");
  els.audioQualityButton.setAttribute("aria-expanded", "false");
  els.audioQualityMenu.classList.add("hidden");
  els.audioQualityMenu.querySelectorAll("[data-quality]").forEach((button) => {
    button.setAttribute("aria-selected", String(button.dataset.quality === state.audioQuality));
  });
}

function toggleAudioQualityMenu() {
  const isOpen = !els.audioQualityMenu.classList.contains("hidden");
  els.audioQualityMenu.classList.toggle("hidden", isOpen);
  els.audioQualityButton.setAttribute("aria-expanded", String(!isOpen));
}

function checkRow({ label, ok, detail, description, required, path, missingText }) {
  const stateClass = ok ? "ok" : required ? "bad" : "warn";
  const stateText = ok ? t("ready") : missingText || t("missing");
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
  return ["streamrip", "ffmpeg"].filter((tool) => !state.setup.tools?.[tool]);
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
  ].join("");
  els.installToolsButton.classList.remove("hidden");
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
  if (event.item_id) row.dataset.itemId = event.item_id;
  const title = display.title ? ` ${display.title}` : "";
  row.innerHTML = `<strong>${display.label}</strong>${title}<br>${display.detail || ""}`;
  els.events.prepend(row);
}

function toDisplayEvent(event) {
  if (event.stage === "lossy_available") {
    return null;
  }
  if (event.stage === "error" || event.stage === "failed") {
    return { label: t("failed"), detail: event.message || event.url };
  }
  return null;
}

function clearItemEvents(itemId) {
  if (!itemId) return;
  els.events.querySelectorAll(`[data-item-id="${CSS.escape(itemId)}"]`).forEach((node) => node.remove());
}

function readUrls() {
  return els.urlInput.value
    .split(/\s+/)
    .map((url) => url.trim())
    .filter(Boolean);
}

function hasCompleteTidalUrl(value) {
  return /tidal\.com\/(album|track)\/\d+(?:\/[A-Za-z0-9_-]+)?(?:[?#]\S*)?$/i.test(value.trim());
}

function hasAnyUrl(value) {
  return /https?:\/\/\S+/i.test(value);
}

function scheduleAutoPreview() {
  if (state.previewTimer) clearTimeout(state.previewTimer);
  const raw = els.urlInput.value.trim();
  if (!raw) {
    els.previewResults.classList.add("hidden");
    els.previewResults.innerHTML = "";
    return;
  }
  state.previewTimer = setTimeout(autoPreviewUrls, 450);
}

async function autoPreviewUrls() {
  const urls = readUrls();
  const invalid = urls.some((url) => hasAnyUrl(url) && !hasCompleteTidalUrl(url));
  const complete = urls.filter(hasCompleteTidalUrl);
  if (invalid || (urls.length && !complete.length && hasAnyUrl(els.urlInput.value))) {
    renderPreviewError(t("previewFailed"));
    return;
  }
  if (!complete.length) return;
  if (state.previewAbort) state.previewAbort.abort();
  state.previewAbort = new AbortController();
  renderPreviewLoading();
  const response = await fetch("/api/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ urls: complete }),
    signal: state.previewAbort.signal,
  });
  const data = await response.json();
  renderPreview(data);
}

function renderPreviewLoading() {
  els.previewResults.classList.remove("hidden");
  els.previewResults.innerHTML = `<div class="preview-state">${t("previewParsing")}</div>`;
}

function renderPreviewError(message) {
  els.previewResults.classList.remove("hidden");
  els.previewResults.innerHTML = `<div class="preview-error">${message}</div>`;
}

function renderPreview(data) {
  els.previewResults.classList.remove("hidden");
  if (!data.items?.length && !data.errors?.length) {
    els.previewResults.textContent = t("previewEmpty");
    return;
  }
  const items = (data.items || []).map((item) => {
    const first = item.tracks[0] || {};
    const cover = previewCoverUrl(first.cover_id);
    const tracks = item.tracks
      .map((track) => `
        <li>
          <span>${track.track_number || ""} ${track.artist || ""} - ${track.title || ""}</span>
          <time>${formatDuration(track.duration_seconds)}</time>
        </li>
      `)
      .join("");
    return `
      <div class="preview-card">
        ${cover ? `<img class="preview-cover" src="${cover}" alt="">` : `<div class="preview-cover preview-cover-empty"></div>`}
        <div class="preview-body">
          <strong>${item.kind === "album" ? item.album_title : first.title || item.item_id}</strong>
          <span>${item.album_artist || first.artist || ""} · ${item.track_count} ${t("tracks")}</span>
          <ul>${tracks}</ul>
        </div>
      </div>
    `;
  });
  const errors = (data.errors || []).map((error) => `<div class="preview-error">${error.url}<br>${error.message}</div>`);
  els.previewResults.innerHTML = [...items, ...errors].join("");
}

function previewCoverUrl(coverId) {
  if (!coverId) return "";
  return `https://resources.tidal.com/images/${String(coverId).replaceAll("-", "/")}/320x320.jpg`;
}

function formatDuration(seconds) {
  const value = Number(seconds || 0);
  if (!value) return "";
  const minutes = Math.floor(value / 60);
  const rest = String(value % 60).padStart(2, "0");
  return `${minutes}:${rest}`;
}

function queuePayload(urls) {
  return {
    urls,
    output_dir: els.outputDir.value,
    concurrency: Number(els.concurrency.value || 10),
    audio_quality: state.audioQuality,
    allow_lossy_audio: false,
    embed_covers: els.embedCovers.checked,
    embed_lyrics: els.embedLyrics.checked,
    write_lrc: els.writeLrc.checked,
    lyrics_mode: els.lyricsMode.value,
    album_template: els.albumTemplate.value,
    filename_template: els.filenameTemplate.value,
    single_filename_template: els.singleFilenameTemplate.value,
    skip_existing: els.existingStrategy.value === "skip",
    existing_strategy: els.existingStrategy.value,
  };
}

async function startDownload() {
  const urls = readUrls();
  if (!urls.length) {
    addEvent({ stage: "error", message: t("pasteAtLeastOne") });
    return;
  }
  if (els.embedCovers.checked && !state.setup?.tools?.metaflac) {
    showCoverToolModal();
    return;
  }
  els.downloadButton.disabled = true;
  els.openFolder.classList.add("hidden");
  els.events.innerHTML = "";
  const response = await fetch("/api/queue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(queuePayload(urls)),
  });
  const data = await response.json();
  state.activeRunId = data.run.id;
  if (els.jobStatus) els.jobStatus.textContent = `Run ${state.activeRunId.slice(0, 8)}`;
  updateRunControls("running");
  state.lastOutputDir = els.outputDir.value;
  await fetch(`/api/queue/runs/${state.activeRunId}/start`, { method: "POST" });
  await refreshQueue();
  listenToRunEvents(state.activeRunId);
}

function listenToRunEvents(runId) {
  if (state.eventSource) state.eventSource.close();
  state.eventSource = new EventSource(`/api/queue/runs/${runId}/events`);
  state.eventSource.onmessage = (message) => {
    const event = JSON.parse(message.data);
    if (event.stage === "lossy_available" && event.item_id) {
      els.downloadButton.disabled = false;
      updateRunControls("failed");
      state.eventSource.close();
      if (confirm(t("lossyConfirm"))) {
        retryQueueItem(event.item_id, { allowLossyAudio: true });
      }
      return;
    }
    if (event.stage === "downloaded") {
      clearItemEvents(event.item_id);
    }
    if (event.stage === "skipped") {
      clearItemEvents(event.item_id);
      showToast(t("existingFileSkipped"), "error", 6000);
    }
    addEvent(event);
    refreshQueue();
    if (event.stage === "complete" || event.stage === "failed") {
      els.downloadButton.disabled = false;
      if (event.stage === "complete") {
        els.openFolder.classList.remove("hidden");
      }
      updateRunControls(event.stage);
      state.eventSource.close();
    }
    if (event.stage === "cancelled" || event.stage === "paused") {
      els.downloadButton.disabled = false;
      updateRunControls(event.stage);
      state.eventSource.close();
    }
  };
}

async function refreshQueue() {
  const response = await fetch(`/api/queue${state.activeRunId ? "?include_transient=true" : ""}`);
  const data = await response.json();
  let items = (data.items || []).filter((item) => Number(item.created_at || 0) >= state.clearedQueueBefore);
  if (state.activeRunId) {
    const byId = new Map();
    items
      .filter((item) => item.status === "complete" || item.run_id === state.activeRunId)
      .forEach((item) => byId.set(item.id, item));
    items = [...byId.values()];
  } else {
    items = items.filter((item) => item.status === "complete");
  }
  renderQueue(items);
}

function clearQueueView() {
  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }
  state.activeRunId = null;
  state.clearedQueueBefore = Date.now() / 1000;
  els.queueTable.innerHTML = "";
  els.events.innerHTML = "";
  els.openFolder.classList.add("hidden");
  updateRunControls("");
}

function renderQueue(items) {
  if (!items.length) {
    els.queueTable.innerHTML = "";
    return;
  }
  els.queueTable.innerHTML = `
    <div class="queue-row queue-head">
      <span>Track</span><span>Progress</span><span>Status</span>
    </div>
    ${items.map(renderQueueRow).join("")}
  `;
}

function renderQueueRow(item) {
  const total = Number(item.progress_total || 0);
  const current = Number(item.progress_current || 0);
  const segmentPercent = total ? Math.round((current / total) * 100) : 0;
  const complete = ["complete", "skipped"].includes(item.status);
  const percent = complete ? 100 : segmentPercent;
  const progressLabel = `${percent}%`;
  const retry = item.status === "failed" ? `<button type="button" class="secondary-button mini-button" data-retry="${item.id}">${t("retry")}</button>` : "";
  const reveal = item.status === "complete" && item.output_path
    ? `<button type="button" class="icon-mini-button" data-reveal-file="${escapeHtml(item.output_path)}" title="${t("openFileLocation")}" aria-label="${t("openFileLocation")}"><img src="/static/folder-open-fill.png" alt=""></button>`
    : "";
  return `
    <div class="queue-row">
      <span><strong>${item.artist || ""} - ${item.title || item.track_id || ""}</strong><small>${item.album_title || ""}</small></span>
      <span class="queue-progress"><span class="progress"><i style="width:${percent}%"></i></span><small>${progressLabel}</small></span>
      <span class="queue-status">${item.status}${retry}${reveal}</span>
    </div>
  `;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function updateRunControls(status) {
  const hasRun = Boolean(state.activeRunId);
  els.pauseRun.classList.toggle("hidden", !hasRun || status !== "running");
  els.resumeRun.classList.toggle("hidden", !hasRun || status !== "paused");
  els.cancelRun.classList.toggle("hidden", !hasRun || !["running", "paused"].includes(status));
  els.exportLog.classList.toggle("hidden", !hasRun);
  if (hasRun) {
    els.exportLog.href = `/api/logs/${state.activeRunId}.txt`;
  }
}

async function retryQueueItem(itemId, options = {}) {
  clearItemEvents(itemId);
  const response = await fetch(`/api/queue/items/${itemId}/retry`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ allow_lossy_audio: Boolean(options.allowLossyAudio) }),
  });
  const data = await response.json();
  if (data.run?.id) {
    state.activeRunId = data.run.id;
    if (els.jobStatus) els.jobStatus.textContent = `Run ${state.activeRunId.slice(0, 8)}`;
    updateRunControls("running");
    listenToRunEvents(state.activeRunId);
  }
  await refreshQueue();
}

async function pauseRun() {
  if (!state.activeRunId) return;
  await fetch(`/api/queue/runs/${state.activeRunId}/pause`, { method: "POST" });
  updateRunControls("paused");
  await refreshQueue();
}

async function resumeRun() {
  if (!state.activeRunId) return;
  await fetch(`/api/queue/runs/${state.activeRunId}/resume`, { method: "POST" });
  updateRunControls("running");
  await refreshQueue();
}

async function cancelRun() {
  if (!state.activeRunId) return;
  await fetch(`/api/queue/runs/${state.activeRunId}/cancel`, { method: "POST" });
  updateRunControls("cancelled");
  await refreshQueue();
}

function addInstallLog(line, command = "", url = "") {
  els.installLog.classList.remove("hidden");
  const row = document.createElement("div");
  row.className = "install-row";
  row.textContent = line;
  const actions = document.createElement("div");
  actions.className = "install-actions";
  if (command) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-command";
    button.textContent = t("copyCommand");
    button.addEventListener("click", async () => {
      await navigator.clipboard.writeText(command);
      showToast(t("commandCopied"), "success", 1600);
    });
    actions.append(button);
  }
  if (url) {
    const link = document.createElement("a");
    link.className = "copy-command";
    link.href = url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = t("officialDownload");
    actions.append(link);
  }
  if (actions.childNodes.length) row.append(actions);
  els.installLog.append(row);
  els.installLog.scrollTop = els.installLog.scrollHeight;
}

async function installMissingTools() {
  if (missingInstallableTools().length === 0) {
    showToast(t("toolsReady"), "success", 2200);
    await refreshSetup();
    return;
  }
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
    addInstallLog(
      event.message || event.label || event.stage,
      event.copy_command || event.manual_command || "",
      event.manual_url || "",
    );
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
  els.installCoverToolButton.disabled = true;
  showToast(t("coverToolInstalling"), "info");
  const response = await fetch("/api/tools/bundled-flac", { method: "POST" });
  const result = await response.json();
  if (result.ok) {
    showToast(t("coverToolInstalled"), "success", 2500);
  } else {
    showToast(result.message || t("bundledFlacMissing"), "error", 5000);
    addInstallLog(result.message || t("bundledFlacMissing"), "", result.manual_url || "");
  }
  els.installCoverToolButton.disabled = false;
  await refreshSetup();
  if (state.setup?.tools?.metaflac) {
    els.embedCovers.checked = true;
    hideCoverToolModal();
  }
}

function showCoverToolModal() {
  els.coverToolModal.classList.remove("hidden");
}

function hideCoverToolModal() {
  els.coverToolModal.classList.add("hidden");
}

function showSettingsModal() {
  els.settingsModal.classList.remove("hidden");
}

function hideSettingsModal() {
  els.settingsModal.classList.add("hidden");
  closeCustomSelectMenus();
}

function selectLabelKey(selectId, value) {
  const keys = {
    lyricsMode: {
      auto: "lyricsAuto",
      synced: "lyricsSynced",
      plain: "lyricsPlain",
    },
    existingStrategy: {
      skip: "strategySkip",
      overwrite: "strategyOverwrite",
      keep_both: "strategyKeepBoth",
    },
  };
  return keys[selectId]?.[value] || "";
}

function customSelectShells() {
  return [...document.querySelectorAll("[data-select-shell]")];
}

function syncCustomSelects() {
  customSelectShells().forEach((shell) => {
    const select = els[shell.dataset.selectTarget];
    if (!select) return;
    const label = shell.querySelector("[data-select-label]");
    const key = selectLabelKey(select.id, select.value);
    if (label) label.textContent = key ? t(key) : select.value;
    shell.querySelectorAll("[data-select-value]").forEach((button) => {
      button.setAttribute("aria-selected", String(button.dataset.selectValue === select.value));
    });
  });
}

function closeCustomSelectMenus(exceptShell = null) {
  customSelectShells().forEach((shell) => {
    if (shell === exceptShell) return;
    shell.querySelector(".quality-menu")?.classList.add("hidden");
    shell.querySelector(".quality-button")?.setAttribute("aria-expanded", "false");
  });
}

function toggleCustomSelect(shell) {
  const menu = shell.querySelector(".quality-menu");
  const button = shell.querySelector(".quality-button");
  const isOpen = !menu.classList.contains("hidden");
  closeCustomSelectMenus(shell);
  menu.classList.toggle("hidden", isOpen);
  button.setAttribute("aria-expanded", String(!isOpen));
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
els.urlInput.addEventListener("input", scheduleAutoPreview);
els.urlInput.addEventListener("paste", () => setTimeout(scheduleAutoPreview, 0));
els.downloadButton.addEventListener("click", startDownload);
els.settingsButton.addEventListener("click", showSettingsModal);
els.closeSettingsButton.addEventListener("click", hideSettingsModal);
els.audioQualityButton.addEventListener("click", toggleAudioQualityMenu);
els.audioQualityMenu.addEventListener("click", (event) => {
  const option = event.target.closest("[data-quality]");
  if (option) setAudioQuality(option.dataset.quality);
});
els.settingsModal.addEventListener("click", (event) => {
  if (event.target === els.settingsModal) hideSettingsModal();
  const selectButton = event.target.closest("[data-select-shell] .quality-button");
  if (selectButton) {
    toggleCustomSelect(selectButton.closest("[data-select-shell]"));
    return;
  }
  const selectOption = event.target.closest("[data-select-value]");
  if (selectOption) {
    const shell = selectOption.closest("[data-select-shell]");
    const select = els[shell.dataset.selectTarget];
    select.value = selectOption.dataset.selectValue;
    select.dispatchEvent(new Event("change", { bubbles: true }));
    syncCustomSelects();
    closeCustomSelectMenus();
  }
});
els.pauseRun.addEventListener("click", pauseRun);
els.resumeRun.addEventListener("click", resumeRun);
els.cancelRun.addEventListener("click", cancelRun);
els.clearQueue.addEventListener("click", clearQueueView);
els.queueTable.addEventListener("click", (event) => {
  const button = event.target.closest("[data-retry]");
  if (button) retryQueueItem(button.dataset.retry);
  const revealButton = event.target.closest("[data-reveal-file]");
  if (revealButton) revealFile(revealButton.dataset.revealFile);
});
els.installToolsButton.addEventListener("click", installMissingTools);
els.installCoverToolButton.addEventListener("click", useBundledFlac);
els.recheckCoverToolButton.addEventListener("click", async () => {
  await refreshSetup();
  if (state.setup?.tools?.metaflac) {
    els.embedCovers.checked = true;
    hideCoverToolModal();
    showToast(t("coverToolInstalled"), "success", 2500);
  }
});
els.cancelCoverToolButton.addEventListener("click", () => {
  els.embedCovers.checked = false;
  hideCoverToolModal();
});
els.recheckButton.addEventListener("click", refreshSetup);
els.embedCovers.addEventListener("change", () => {
  if (els.embedCovers.checked && !state.setup?.tools?.metaflac) {
    els.embedCovers.checked = false;
    showCoverToolModal();
  }
});
els.workspaceAccountButton.addEventListener("click", toggleAccountMenu);
els.unbindButton.addEventListener("click", unbindTidal);
document.addEventListener("click", (event) => {
  if (!els.workspaceAccountButton.contains(event.target) && !els.accountDropdown.contains(event.target)) {
    closeAccountMenu();
  }
  if (!els.audioQualityButton.contains(event.target) && !els.audioQualityMenu.contains(event.target)) {
    els.audioQualityMenu.classList.add("hidden");
    els.audioQualityButton.setAttribute("aria-expanded", "false");
  }
  if (!event.target.closest("[data-select-shell]")) {
    closeCustomSelectMenus();
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeAccountMenu();
    els.audioQualityMenu.classList.add("hidden");
    els.audioQualityButton.setAttribute("aria-expanded", "false");
    closeCustomSelectMenus();
  }
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

async function revealFile(path) {
  await fetch("/api/folders/reveal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  });
}
refreshSetup().catch((error) => {
  els.bindMessage.textContent = `Startup failed: ${error.message}`;
});
refreshQueue().catch(() => {});
applyLanguage();
setAudioQuality(state.audioQuality);
