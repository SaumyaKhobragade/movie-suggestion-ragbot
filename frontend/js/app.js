const form = document.getElementById("query-form");
const promptInput = document.getElementById("prompt");
const topKInput = document.getElementById("top-k");
const summarizeInput = document.getElementById("summarize");
const resultsSection = document.getElementById("results");
const summarySection = document.getElementById("summary");
const statusLabel = document.getElementById("status");
const submitButton = form.querySelector("button");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt) {
    statusLabel.textContent = "Please enter a prompt.";
    return;
  }

  const topK = Number(topKInput.value) || 3;
  const summarize = summarizeInput.checked;

  submitButton.disabled = true;
  statusLabel.textContent = "Searching...";
  summarySection.hidden = true;
  summarySection.textContent = "";
  resultsSection.replaceChildren();

  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, top_k: topK, summarize })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || "Search failed");
    }

    const payload = await response.json();
    renderResults(payload);
    statusLabel.textContent = `Found ${payload.results.length} result(s).`;
  } catch (error) {
    console.error(error);
    statusLabel.textContent = error.message || "Failed to retrieve results.";
  } finally {
    submitButton.disabled = false;
  }
});

function renderResults(payload) {
  resultsSection.replaceChildren();
  (payload.results || []).forEach((item) => {
    const card = document.createElement("article");
    card.className = "card";

    const title = document.createElement("h2");
    title.textContent = item.title || "Untitled";

    const meta = document.createElement("p");
    meta.className = "meta";
    const genre = item.genre ? `Genre: ${item.genre}` : "Genre: n/a";
    const year = item.release_year ? `Year: ${item.release_year}` : "Year: n/a";
    const score = `Score: ${item.score.toFixed(4)}`;
    meta.textContent = `${genre} • ${year} • ${score}`;

    const details = document.createElement("pre");
    details.textContent = JSON.stringify(item.payload, null, 2);

    card.append(title, meta, details);
    resultsSection.appendChild(card);
  });

  if (payload.summary) {
    summarySection.hidden = false;
    summarySection.textContent = payload.summary;
  }
}
