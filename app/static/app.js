const state = {
  setup: null,
  authSession: null,
  eventSource: null,
  language: localStorage.getItem("language") || "en",
  lastOutputDir: null,
};

const els = {
  langEn: document.querySelector("#langEn"),
  langZh: document.querySelector("#langZh"),
  boundStatus: document.querySelector("#boundStatus"),
  setupPanel: document.querySelector("#setupPanel"),
  workspace: document.querySelector("#workspace"),
  checks: document.querySelector("#checks"),
  bindButton: document.querySelector("#bindButton"),
  bindMessage: document.querySelector("#bindMessage"),
  tokenMessage: document.querySelector("#tokenMessage"),
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
};

const copy = {
  en: {
    ready: "Ready",
    missing: "Missing",
    checkingBinding: "Checking binding...",
    bound: "Bound to Tidal",
    notBound: "Tidal not bound",
    step1: "Step 1",
    step2: "Step 2",
    step3: "Step 3",
    checkChain: "Check the chain",
    checkChainCopy: "The app needs local tools and a streamrip-compatible config before it can bind Tidal.",
    bindTidal: "Bind Tidal",
    bindTidalCopy: "Open Tidal's official authorization page. You sign in there; this app never sees your password.",
    startBinding: "Start Tidal binding",
    confirmToken: "Confirm token",
    confirmTokenCopy: "After authorization, this page automatically detects the token and unlocks the downloader.",
    waitingBinding: "Waiting for binding.",
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
    step1: "步骤 1",
    step2: "步骤 2",
    step3: "步骤 3",
    checkChain: "检查环境",
    checkChainCopy: "应用需要本地工具和 streamrip 兼容配置，然后才能绑定 Tidal。",
    bindTidal: "绑定 Tidal",
    bindTidalCopy: "打开 Tidal 官方授权页。你在那里登录，本应用不会看到你的密码。",
    startBinding: "开始绑定 Tidal",
    confirmToken: "确认 token",
    confirmTokenCopy: "授权后，本页面会自动检测 token，并解锁下载台。",
    waitingBinding: "等待绑定。",
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

function checkRow(label, ok, detail) {
  return `<div class="check"><strong>${label}</strong><br><span class="${ok ? "ok" : "bad"}">${ok ? t("ready") : t("missing")}</span> ${detail || ""}</div>`;
}

async function refreshSetup() {
  const response = await fetch("/api/setup/status");
  state.setup = await response.json();
  els.outputDir.value = state.setup.output_dir;
  renderChecks();
  renderMode();
}

function renderChecks() {
  els.checks.innerHTML = [
    checkRow("ffmpeg", state.setup.tools.ffmpeg, "required for FLAC output"),
    checkRow("metaflac", state.setup.tools.metaflac, "required for embedded covers"),
    checkRow("streamrip config", state.setup.streamrip_config.exists, state.setup.streamrip_config.path),
    checkRow("Tidal token", state.setup.tidal.bound, state.setup.tidal.country_code || "not bound"),
  ].join("");
}

function renderMode() {
  const bound = Boolean(state.setup?.tidal?.bound);
  els.boundStatus.textContent = bound
    ? `${t("bound")} (${state.setup.tidal.country_code})`
    : t("notBound");
  els.setupPanel.classList.toggle("hidden", bound);
  els.workspace.classList.toggle("hidden", !bound);
}

async function startBinding() {
  els.bindButton.disabled = true;
  els.bindMessage.textContent = t("creatingLink");
  const response = await fetch("/api/auth/tidal/start", { method: "POST" });
  state.authSession = await response.json();
  els.bindMessage.innerHTML = `${t("opened")} <a href="${state.authSession.url}" target="_blank" rel="noreferrer">${state.authSession.url}</a>`;
  window.open(state.authSession.url, "_blank", "noopener,noreferrer");
  pollBinding();
}

async function pollBinding() {
  if (!state.authSession) return;
  const response = await fetch(`/api/auth/tidal/status/${state.authSession.session_id}`);
  const data = await response.json();
  els.tokenMessage.textContent = `${t("status")}: ${data.status}`;
  if (data.status === "success") {
    await refreshSetup();
    els.bindButton.disabled = false;
    return;
  }
  if (data.status === "expired" || data.status === "error") {
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

els.bindButton.addEventListener("click", startBinding);
els.downloadButton.addEventListener("click", startDownload);
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
  els.boundStatus.textContent = `Startup failed: ${error.message}`;
});
applyLanguage();
