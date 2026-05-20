async function boot() {
  const root = document.querySelector("#app");
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    root.textContent = data.ok ? "Backend connected." : "Backend unavailable.";
  } catch (error) {
    root.textContent = `Backend unavailable: ${error.message}`;
  }
}

boot();
