const form = document.getElementById("query-form");
const promptInput = document.getElementById("prompt");
const topKInput = document.getElementById("top-k");
const resultsSection = document.getElementById("results");
const statusLabel = document.getElementById("status");
const submitButton = form.querySelector("button");

function humanizeKey(key) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .replace(/\s{2,}/g, " ");
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "number") {
    if (Math.abs(value) >= 1_000_000) {
      return `${(value / 1_000_000).toFixed(2)} M`;
    }
    return value.toLocaleString();
  }

  if (Array.isArray(value)) {
    return value.length ? value.join(", ") : "—";
  }

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

function buildDetailsTable(payload) {
  const table = document.createElement("table");
  table.className = "data-table";

  const tbody = document.createElement("tbody");

  Object.entries(payload || {}).forEach(([rawKey, rawValue]) => {
    const row = document.createElement("tr");

    const keyCell = document.createElement("th");
    keyCell.scope = "row";
    keyCell.textContent = humanizeKey(rawKey);

    const valueCell = document.createElement("td");
    const formattedValue = formatValue(rawValue);

    if (typeof rawValue === "object" && rawValue !== null && !Array.isArray(rawValue)) {
      const code = document.createElement("pre");
      code.textContent = formattedValue;
      valueCell.appendChild(code);
    } else {
      valueCell.textContent = formattedValue;
    }

    row.append(keyCell, valueCell);
    tbody.appendChild(row);
  });

  if (!tbody.children.length) {
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");
    emptyCell.colSpan = 2;
    emptyCell.textContent = "No additional details available.";
    emptyRow.appendChild(emptyCell);
    tbody.appendChild(emptyRow);
  }

  table.appendChild(tbody);
  return table;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt) {
    statusLabel.textContent = "Please enter a prompt.";
    return;
  }

  const topK = Number(topKInput.value) || 3;

  submitButton.disabled = true;
  statusLabel.textContent = "Searching...";
  resultsSection.replaceChildren();

  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, top_k: topK })
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
  (payload.results || []).forEach((item, index) => {
    const card = document.createElement("article");
    card.className = "card result-card";
    card.style.setProperty("--stagger-delay", `${index * 140}ms`);

    const title = document.createElement("h2");
    title.textContent = item.title || "Untitled";

    const meta = document.createElement("p");
    meta.className = "meta";
    const genre = item.genre ? `Genre: ${item.genre}` : "Genre: n/a";
    const year = item.release_year ? `Year: ${item.release_year}` : "Year: n/a";
    const score = `Score: ${item.score.toFixed(4)}`;
    meta.textContent = `${genre} • ${year} • ${score}`;

    const detailTable = buildDetailsTable(item.payload || {});

    card.append(title, meta, detailTable);
    resultsSection.appendChild(card);
  });
}
