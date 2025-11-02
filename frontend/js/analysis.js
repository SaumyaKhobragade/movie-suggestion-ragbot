const palette = {
    background: "rgba(135, 247, 255, 0.18)",
    border: "rgba(135, 247, 255, 0.9)",
    secondaryBackground: "rgba(91, 141, 239, 0.18)",
    secondaryBorder: "rgba(91, 141, 239, 0.9)",
    accent: "rgba(255, 127, 156, 0.9)",
};

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: {
                color: "#f1f5ff",
                font: { size: 13 },
            },
        },
        tooltip: {
            backgroundColor: "rgba(10, 20, 40, 0.85)",
            titleColor: "#e5eeff",
            bodyColor: "#e5eeff",
        },
    },
    scales: {
        x: {
            ticks: { color: "#d9e5ff" },
            grid: { color: "rgba(100, 140, 200, 0.15)" },
        },
        y: {
            ticks: { color: "#d9e5ff" },
            grid: { color: "rgba(100, 140, 200, 0.1)" },
        },
    },
};

async function loadAnalytics() {
    const response = await fetch("/api/analysis");
    if (!response.ok) {
        throw new Error("Failed to load analytics");
    }
    return response.json();
}

function renderTopGenres(canvas, topGenres) {
    const labels = topGenres.map((item) => item.genre);
    const data = topGenres.map((item) => item.average_profit);

    new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Average Profit ($M)",
                    data,
                    backgroundColor: palette.background,
                    borderColor: palette.border,
                    borderWidth: 2,
                    borderRadius: 8,
                },
            ],
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    ticks: {
                        ...chartOptions.scales.y.ticks,
                        callback: (value) => `${value.toFixed(0)}M`,
                    },
                },
            },
        },
    });
}

function renderProfitMargins(canvas, margins) {
    const labels = margins.map((item) => item.genre);
    const data = margins.map((item) => item.median_margin * 100);

    new Chart(canvas, {
        type: "radar",
        data: {
            labels,
            datasets: [
                {
                    label: "Median Profit Margin",
                    data,
                    backgroundColor: palette.secondaryBackground,
                    borderColor: palette.secondaryBorder,
                    pointBackgroundColor: palette.border,
                    borderWidth: 2,
                },
            ],
        },
        options: {
            ...chartOptions,
            elements: {
                line: { borderWidth: 2 },
            },
            scales: {
                r: {
                    angleLines: { color: "rgba(100, 140, 200, 0.25)" },
                    grid: { color: "rgba(100, 140, 200, 0.2)" },
                    pointLabels: { color: "#d9e5ff" },
                    ticks: {
                        display: true,
                        color: "#d9e5ff",
                        callback: (value) => `${Math.round(value)}%`,
                    },
                },
            },
        },
    });
}

function renderRevenueTrend(canvas, series) {
    const labels = series.map((item) => item.release_year);
    const revenue = series.map((item) => item.average_revenue);
    const profit = series.map((item) => item.average_profit);

    new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Average Revenue ($M)",
                    data: revenue,
                    borderColor: palette.border,
                    backgroundColor: "rgba(91, 141, 239, 0.15)",
                    fill: true,
                    tension: 0.35,
                },
                {
                    label: "Average Profit ($M)",
                    data: profit,
                    borderColor: palette.accent,
                    backgroundColor: "rgba(255, 127, 156, 0.12)",
                    fill: true,
                    tension: 0.35,
                },
            ],
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    ticks: {
                        ...chartOptions.scales.y.ticks,
                        callback: (value) => `${value.toFixed(0)}M`,
                    },
                },
            },
        },
    });
}

function renderCorrelation(canvas, pairs) {
    const labels = pairs.map((item) => item.pair);
    const data = pairs.map((item) => item.value);

    new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Correlation coefficient",
                    data,
                    backgroundColor: data.map((value) =>
                        value >= 0 ? "rgba(91, 141, 239, 0.6)" : "rgba(255, 127, 156, 0.55)"
                    ),
                    borderColor: data.map((value) =>
                        value >= 0 ? "rgba(91, 141, 239, 0.9)" : "rgba(255, 127, 156, 0.9)"
                    ),
                    borderWidth: 2,
                    borderRadius: 6,
                },
            ],
        },
        options: {
            ...chartOptions,
            indexAxis: "y",
            scales: {
                x: {
                    min: -1,
                    max: 1,
                    ticks: {
                        color: "#d9e5ff",
                        callback: (value) => value.toFixed(1),
                    },
                    grid: { color: "rgba(100, 140, 200, 0.2)" },
                },
                y: {
                    ticks: { color: "#d9e5ff" },
                    grid: { display: false },
                },
            },
        },
    });
}

function renderStandoutMovies(container, movies) {
    container.innerHTML = "";
    movies.forEach((movie) => {
        const element = document.createElement("div");
        element.className = "standout-item";
        element.innerHTML = `
            <div>
                <h3>${movie.title}</h3>
                <span>${movie.genre} · ${movie.release_year}</span>
            </div>
            <div>
                <span><strong>${movie.profit.toFixed(1)}M</strong> profit</span><br />
                <span>${movie.revenue.toFixed(1)}M revenue · ${(movie.margin * 100).toFixed(0)}% ROI</span>
            </div>
        `;
        container.appendChild(element);
    });
}

async function initializeDashboard() {
    try {
        const data = await loadAnalytics();

        renderTopGenres(document.querySelector("#top-genres canvas"), data.top_genres_average_profit);
        renderProfitMargins(document.querySelector("#profit-margins canvas"), data.median_profit_margin_by_genre);
        renderRevenueTrend(document.querySelector("#revenue-trend canvas"), data.revenue_profit_trend);
        renderCorrelation(document.querySelector("#correlation canvas"), data.metric_correlations);
        renderStandoutMovies(
            document.querySelector("#standouts .standout-list"),
            data.top_movies_by_profit_and_margin
        );
    } catch (error) {
        console.error(error);
        alert("Unable to load analytics right now. Please try again later.");
    }
}

document.addEventListener("DOMContentLoaded", initializeDashboard);
