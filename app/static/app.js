const state = {
  setup: null,
  authSession: null,
  eventSource: null,
};

const els = {
  boundStatus: document.querySelector("#boundStatus"),
  setupPanel: document.querySelector("#setupPanel"),
  workspace: document.querySelector("#workspace"),
  checks: document.querySelector("#checks"),
  bindButton: document.querySelector("#bindButton"),
  bindMessage: document.querySelector("#bindMessage"),
  tokenMessage: document.querySelector("#tokenMessage"),
  urlInput: document.querySelector("#urlInput"),
  outputDir: document.querySelector("#outputDir"),
  concurrency: document.querySelector("#concurrency"),
  embedCovers: document.querySelector("#embedCovers"),
  skipExisting: document.querySelector("#skipExisting"),
  downloadButton: document.querySelector("#downloadButton"),
  events: document.querySelector("#events"),
  jobStatus: document.querySelector("#jobStatus"),
};

function checkRow(label, ok, detail) {
  return `<div class="check"><strong>${label}</strong><br><span class="${ok ? "ok" : "bad"}">${ok ? "Ready" : "Missing"}</span> ${detail || ""}</div>`;
}

async function refreshSetup() {
  const response = await fetch("/api/setup/status");
  state.setup = await response.json();
  els.outputDir.value = state.setup.output_dir;
  els.checks.innerHTML = [
    checkRow("ffmpeg", state.setup.tools.ffmpeg, "required for FLAC output"),
    checkRow("metaflac", state.setup.tools.metaflac, "required for embedded covers"),
    checkRow("streamrip config", state.setup.streamrip_config.exists, state.setup.streamrip_config.path),
    checkRow("Tidal token", state.setup.tidal.bound, state.setup.tidal.country_code || "not bound"),
  ].join("");
  renderMode();
}

function renderMode() {
  const bound = Boolean(state.setup?.tidal?.bound);
  els.boundStatus.textContent = bound
    ? `Bound to Tidal (${state.setup.tidal.country_code})`
    : "Tidal not bound";
  els.setupPanel.classList.toggle("hidden", bound);
  els.workspace.classList.toggle("hidden", !bound);
}

async function startBinding() {
  els.bindButton.disabled = true;
  els.bindMessage.textContent = "Creating Tidal authorization link...";
  const response = await fetch("/api/auth/tidal/start", { method: "POST" });
  state.authSession = await response.json();
  els.bindMessage.innerHTML = `Opened <a href="${state.authSession.url}" target="_blank" rel="noreferrer">${state.authSession.url}</a>`;
  window.open(state.authSession.url, "_blank", "noopener,noreferrer");
  pollBinding();
}

async function pollBinding() {
  if (!state.authSession) return;
  const response = await fetch(`/api/auth/tidal/status/${state.authSession.session_id}`);
  const data = await response.json();
  els.tokenMessage.textContent = `Status: ${data.status}`;
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
  const row = document.createElement("div");
  row.className = "event";
  const title = event.title ? ` ${event.artist || ""} - ${event.title}` : "";
  row.innerHTML = `<strong>${event.stage}</strong>${title}<br>${event.message || event.path || event.url || ""}`;
  els.events.prepend(row);
}

async function startDownload() {
  const urls = els.urlInput.value
    .split(/\s+/)
    .map((url) => url.trim())
    .filter(Boolean);
  if (!urls.length) {
    addEvent({ stage: "error", message: "Paste at least one Tidal URL." });
    return;
  }
  els.downloadButton.disabled = true;
  els.events.innerHTML = "";
  const response = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      urls,
      output_dir: els.outputDir.value,
      concurrency: Number(els.concurrency.value || 10),
      embed_covers: els.embedCovers.checked,
      skip_existing: els.skipExisting.checked,
    }),
  });
  const job = await response.json();
  els.jobStatus.textContent = `Job ${job.job_id.slice(0, 8)}`;
  if (state.eventSource) state.eventSource.close();
  state.eventSource = new EventSource(`/api/jobs/${job.job_id}/events`);
  state.eventSource.onmessage = (message) => {
    const event = JSON.parse(message.data);
    addEvent(event);
    if (event.stage === "complete" || event.stage === "failed") {
      els.downloadButton.disabled = false;
      state.eventSource.close();
    }
  };
}

els.bindButton.addEventListener("click", startBinding);
els.downloadButton.addEventListener("click", startDownload);
refreshSetup().catch((error) => {
  els.boundStatus.textContent = `Startup failed: ${error.message}`;
});
