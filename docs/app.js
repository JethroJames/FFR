(function () {
  const data = window.FFR_PROJECT;
  const state = {
    view: "comparison",
    metric: "mmvu",
    caseId: data.cases[0].id
  };

  const toneMap = {
    brand: "#0f7f87",
    accent: "#ef8a62",
    gold: "#f3c244",
    plum: "#a058b8",
    muted: "#8d98a5"
  };

  const viewMeta = {
    comparison: {
      label: "Table 2",
      title: "Main benchmark comparison",
      caption: "Key baselines and FFR-enhanced variants across the paper's benchmark suite.",
      metrics: data.metrics.map((item) => item.key)
    },
    ablation: {
      label: "Table 3",
      title: "Ablation of the FFR recipe",
      caption: "Removing visual context, GT reference, or the full repair mechanism degrades the final result.",
      metrics: data.metrics.map((item) => item.key)
    },
    teacher: {
      label: "Table 7 / Table 9",
      title: "Teacher model selection",
      caption: "Teaching quality depends on more than raw size. Different teachers win on different subsets of the benchmark suite.",
      metrics: data.metrics.map((item) => item.key).concat("avg")
    },
    sensitivity: {
      label: "Figure 7 / Table 10",
      title: "Patch-tax sensitivity",
      caption: "kappa governs how strongly repaired rollouts are discounted. The sweet spot is near kappa=0.3.",
      metrics: ["avg"].concat(data.metrics.map((item) => item.key))
    }
  };

  function metricLabel(metricKey) {
    if (metricKey === "avg") {
      return "Average";
    }
    const found = data.metrics.find((item) => item.key === metricKey);
    return found ? found.label : metricKey;
  }

  function setText(id, value) {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = value;
    }
  }

  function renderLinks(targetId, links) {
    const root = document.getElementById(targetId);
    root.innerHTML = "";

    links.forEach((link) => {
      const anchor = document.createElement("a");
      anchor.className = `action-link ${link.style || "ghost"}${link.url ? "" : " is-disabled"}`;
      anchor.textContent = link.label;
      anchor.href = link.url || "#";
      if (link.url) {
        anchor.target = "_blank";
        anchor.rel = "noreferrer";
      } else {
        anchor.setAttribute("aria-disabled", "true");
      }
      root.appendChild(anchor);
    });
  }

  function renderHero() {
    setText("venue-line", data.meta.venue);
    setText("project-title", data.meta.title);
    setText("project-subtitle", data.meta.subtitle);
    setText("author-line", data.meta.authors.join(" · "));
    setText("hero-summary", data.meta.summary);
    setText("abstract-text", data.abstract);
    setText("bibtex-block", data.bibtex);
    renderLinks("hero-actions", data.meta.links);
    renderLinks("resource-links", data.meta.links);

    const statsRoot = document.getElementById("hero-stats");
    statsRoot.innerHTML = "";
    data.meta.heroStats.forEach((item) => {
      const card = document.createElement("div");
      card.className = "stat-card";
      card.innerHTML = `<strong>${item.value}</strong><span>${item.label}</span><span>${item.note}</span>`;
      statsRoot.appendChild(card);
    });

    const regimeRoot = document.getElementById("regime-grid");
    regimeRoot.innerHTML = "";
    data.regimes.forEach((item) => {
      const card = document.createElement("div");
      card.className = `regime-card${item.active ? " active" : ""}`;
      card.innerHTML = `<h3>${item.title}</h3><p>${item.body}</p>`;
      regimeRoot.appendChild(card);
    });

    const insightRoot = document.getElementById("insight-list");
    insightRoot.innerHTML = "";
    data.insights.forEach((item) => {
      const block = document.createElement("div");
      block.className = "insight-item";
      block.innerHTML = `<h3>${item.title}</h3><p>${item.body}</p>`;
      insightRoot.appendChild(block);
    });

    const methodRoot = document.getElementById("method-stack");
    methodRoot.innerHTML = "";
    data.methodSteps.forEach((item) => {
      const block = document.createElement("div");
      block.className = "method-item";
      block.dataset.step = item.step;
      block.innerHTML = `<h3>${item.title}</h3><p>${item.body}</p>`;
      methodRoot.appendChild(block);
    });
  }

  function renderViewToggles() {
    const root = document.getElementById("view-toggles");
    root.innerHTML = "";
    Object.keys(viewMeta).forEach((viewKey) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `toggle-pill${state.view === viewKey ? " is-active" : ""}`;
      button.textContent = viewMeta[viewKey].title;
      button.addEventListener("click", () => {
        state.view = viewKey;
        const validMetrics = viewMeta[viewKey].metrics;
        if (!validMetrics.includes(state.metric)) {
          state.metric = validMetrics[0];
        }
        renderResults();
      });
      root.appendChild(button);
    });
  }

  function renderMetricToggles() {
    const root = document.getElementById("metric-toggles");
    root.innerHTML = "";
    viewMeta[state.view].metrics.forEach((metricKey) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `toggle-pill${state.metric === metricKey ? " is-active" : ""}`;
      button.textContent = metricLabel(metricKey);
      button.addEventListener("click", () => {
        state.metric = metricKey;
        renderResults();
      });
      root.appendChild(button);
    });
  }

  function valueFor(item, metricKey) {
    return item.values[metricKey];
  }

  function formatValue(value) {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return "-";
    }
    const normalized = Math.round(value * 100) / 100;
    return Number.isInteger(normalized) ? `${normalized}` : normalized.toFixed(2);
  }

  function renderBarChart(items, metricKey) {
    const svg = document.getElementById("results-chart");
    const valid = items.filter((item) => Number.isFinite(valueFor(item, metricKey)));
    const width = 900;
    const labelWidth = 240;
    const chartWidth = 520;
    const startX = 260;
    const top = 56;
    const rowHeight = 50;
    const barHeight = 22;
    const height = top + valid.length * rowHeight + 58;
    const ticks = [0, 20, 40, 60, 80];

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.innerHTML = "";

    ticks.forEach((tick) => {
      const x = startX + (chartWidth * tick) / 80;
      const grid = document.createElementNS("http://www.w3.org/2000/svg", "line");
      grid.setAttribute("x1", x);
      grid.setAttribute("x2", x);
      grid.setAttribute("y1", top - 20);
      grid.setAttribute("y2", height - 28);
      grid.setAttribute("class", "chart-grid");
      svg.appendChild(grid);

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", x);
      label.setAttribute("y", top - 30);
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("class", "chart-axis");
      label.textContent = `${tick}`;
      svg.appendChild(label);
    });

    valid.forEach((item, index) => {
      const y = top + index * rowHeight;
      const score = valueFor(item, metricKey);
      const tone = toneMap[item.tone] || toneMap.muted;

      const name = document.createElementNS("http://www.w3.org/2000/svg", "text");
      name.setAttribute("x", 16);
      name.setAttribute("y", y + 16);
      name.setAttribute("class", "chart-label");
      name.textContent = item.label;
      svg.appendChild(name);

      const track = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      track.setAttribute("x", startX);
      track.setAttribute("y", y);
      track.setAttribute("width", chartWidth);
      track.setAttribute("height", barHeight);
      track.setAttribute("rx", "12");
      track.setAttribute("class", "chart-track");
      svg.appendChild(track);

      const bar = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      bar.setAttribute("x", startX);
      bar.setAttribute("y", y);
      bar.setAttribute("width", (chartWidth * score) / 80);
      bar.setAttribute("height", barHeight);
      bar.setAttribute("fill", tone);
      bar.setAttribute("class", "chart-bar");
      svg.appendChild(bar);

      const value = document.createElementNS("http://www.w3.org/2000/svg", "text");
      value.setAttribute("x", startX + chartWidth + 70);
      value.setAttribute("y", y + 16);
      value.setAttribute("text-anchor", "end");
      value.setAttribute("class", "chart-value");
      value.textContent = formatValue(score);
      svg.appendChild(value);
    });
  }

  function renderLineChart(items, metricKey) {
    const svg = document.getElementById("results-chart");
    const width = 900;
    const height = 520;
    const margin = { top: 46, right: 80, bottom: 70, left: 76 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    const avgValues = items.map((item) => item.values.avg);
    const metricValues = items.map((item) => item.values[metricKey]);
    const allValues = metricKey === "avg" ? avgValues : avgValues.concat(metricValues);
    const minValue = Math.min.apply(null, allValues) - 1.4;
    const maxValue = Math.max.apply(null, allValues) + 1.4;

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.innerHTML = "";

    function xScale(index) {
      if (items.length === 1) {
        return margin.left + innerWidth / 2;
      }
      return margin.left + (innerWidth * index) / (items.length - 1);
    }

    function yScale(value) {
      return margin.top + innerHeight - ((value - minValue) / (maxValue - minValue)) * innerHeight;
    }

    for (let t = 0; t < 5; t += 1) {
      const ratio = t / 4;
      const value = minValue + (maxValue - minValue) * ratio;
      const y = yScale(value);

      const grid = document.createElementNS("http://www.w3.org/2000/svg", "line");
      grid.setAttribute("x1", margin.left);
      grid.setAttribute("x2", width - margin.right);
      grid.setAttribute("y1", y);
      grid.setAttribute("y2", y);
      grid.setAttribute("class", "chart-grid");
      svg.appendChild(grid);

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", margin.left - 10);
      label.setAttribute("y", y + 4);
      label.setAttribute("text-anchor", "end");
      label.setAttribute("class", "chart-axis");
      label.textContent = formatValue(value);
      svg.appendChild(label);
    }

    const axis = document.createElementNS("http://www.w3.org/2000/svg", "line");
    axis.setAttribute("x1", margin.left);
    axis.setAttribute("x2", width - margin.right);
    axis.setAttribute("y1", height - margin.bottom);
    axis.setAttribute("y2", height - margin.bottom);
    axis.setAttribute("class", "line-axis");
    svg.appendChild(axis);

    items.forEach((item, index) => {
      const x = xScale(index);
      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", x);
      label.setAttribute("y", height - margin.bottom + 28);
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("class", "chart-axis");
      label.textContent = item.kappa.toFixed(1);
      svg.appendChild(label);
    });

    const lines = [{ key: "avg", color: toneMap.brand, label: "Average" }];
    if (metricKey !== "avg") {
      lines.push({ key: metricKey, color: toneMap.accent, label: metricLabel(metricKey) });
    }

    lines.forEach((line, lineIndex) => {
      const points = items.map((item, index) => `${xScale(index)},${yScale(item.values[line.key])}`).join(" ");
      const path = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
      path.setAttribute("points", points);
      path.setAttribute("class", "line-path");
      path.setAttribute("stroke", line.color);
      svg.appendChild(path);

      items.forEach((item, index) => {
        const point = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        point.setAttribute("cx", xScale(index));
        point.setAttribute("cy", yScale(item.values[line.key]));
        point.setAttribute("r", 5.5);
        point.setAttribute("fill", line.color);
        point.setAttribute("class", "line-point");
        svg.appendChild(point);
      });

      const legendX = width - margin.right + 6;
      const legendY = margin.top + 22 + lineIndex * 24;
      const swatch = document.createElementNS("http://www.w3.org/2000/svg", "line");
      swatch.setAttribute("x1", legendX);
      swatch.setAttribute("x2", legendX + 24);
      swatch.setAttribute("y1", legendY);
      swatch.setAttribute("y2", legendY);
      swatch.setAttribute("stroke", line.color);
      swatch.setAttribute("stroke-width", "4");
      swatch.setAttribute("stroke-linecap", "round");
      svg.appendChild(swatch);

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", legendX + 32);
      text.setAttribute("y", legendY + 4);
      text.setAttribute("class", "chart-axis");
      text.textContent = line.label;
      svg.appendChild(text);
    });
  }

  function computeNotes(items, metricKey) {
    const valid = items
      .filter((item) => Number.isFinite(valueFor(item, metricKey)))
      .map((item) => ({ label: item.label, value: valueFor(item, metricKey) }))
      .sort((a, b) => b.value - a.value);
    const top = valid[0];

    if (state.view === "comparison") {
      const base = items.find((item) => item.label === "Video-R1");
      const ffr = items.find((item) => item.label === "FFR (Video-R1)");
      return [
        `${metricLabel(metricKey)} leader in this view: ${top.label} (${formatValue(top.value)}).`,
        `FFR lifts Video-R1 from ${formatValue(valueFor(base, metricKey))} to ${formatValue(valueFor(ffr, metricKey))} on ${metricLabel(metricKey)}.`,
        "The repair benefit is especially visible on long-horizon and causal benchmarks where first-pass salience is often misleading."
      ];
    }

    if (state.view === "ablation") {
      const full = items.find((item) => item.label === "Full model");
      const noVisual = items.find((item) => item.label === "w./ FFR (no visual context)");
      const noGt = items.find((item) => item.label === "w./ FFR (no GT reference)");
      return [
        `Full model score: ${formatValue(valueFor(full, metricKey))}.`,
        `Removing visual context drops the score to ${formatValue(valueFor(noVisual, metricKey))}, showing that the patch must point to actual evidence.`,
        `The no-GT-reference variant still helps (${formatValue(valueFor(noGt, metricKey))}), which suggests the mechanism is not just copying labels.`
      ];
    }

    if (state.view === "teacher") {
      const bestAvg = items.filter((item) => Number.isFinite(item.values.avg)).sort((a, b) => b.values.avg - a.values.avg)[0];
      return [
        `${top.label} is best on ${metricLabel(metricKey)} in this panel with ${formatValue(top.value)}.`,
        `${bestAvg.label} has the strongest overall average (${formatValue(bestAvg.values.avg)}).`,
        "Teacher quality depends on diagnosis and guidance style, not just parameter count."
      ];
    }

    const best = items.map((item) => ({ kappa: item.kappa, value: item.values[metricKey] })).sort((a, b) => b.value - a.value)[0];
    return [
      `Best ${metricLabel(metricKey)} score occurs at kappa=${best.kappa.toFixed(1)} (${formatValue(best.value)}).`,
      "Too small a patch tax encourages over-reliance on repair; too large a tax suppresses useful guidance.",
      "The average score peaks at kappa=0.3, which matches the paper's recommended setting."
    ];
  }

  function renderResults() {
    renderViewToggles();
    renderMetricToggles();

    const meta = viewMeta[state.view];
    const series = data.results[state.view];

    setText("chart-label", meta.label);
    setText("chart-title", `${meta.title} · ${metricLabel(state.metric)}`);
    setText("chart-caption", meta.caption);
    setText("results-table-head", metricLabel(state.metric));

    if (state.view === "sensitivity") {
      renderLineChart(series, state.metric);
    } else {
      renderBarChart(series, state.metric);
    }

    const notesRoot = document.getElementById("results-notes");
    notesRoot.innerHTML = `<ul>${computeNotes(series, state.metric).map((note) => `<li>${note}</li>`).join("")}</ul>`;

    const body = document.getElementById("results-table-body");
    body.innerHTML = "";
    series
      .filter((item) => Number.isFinite(valueFor(item, state.metric)))
      .sort((a, b) => valueFor(b, state.metric) - valueFor(a, state.metric))
      .forEach((item) => {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${item.label}</td><td>${formatValue(valueFor(item, state.metric))}</td>`;
        body.appendChild(row);
      });
  }

  function renderCaseNav() {
    const root = document.getElementById("case-nav");
    root.innerHTML = "";
    data.cases.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `case-button${state.caseId === item.id ? " is-active" : ""}`;
      button.innerHTML = `<strong>${item.title}</strong><span>${item.tag}</span>`;
      button.addEventListener("click", () => {
        state.caseId = item.id;
        renderCases();
      });
      root.appendChild(button);
    });
  }

  function renderPipelineCase(item) {
    document.getElementById("case-visual").innerHTML = `<img src="${item.image}" alt="${item.title}">`;
    document.getElementById("case-story").innerHTML = `
      <div class="story-block">
        <h4>Question</h4>
        <p>${item.question}</p>
        <div style="margin-top: 12px;">${item.options.map((option) => `<span class="question-chip">${option}</span>`).join("")}</div>
      </div>
      <div class="story-block">
        <h4>${item.original.title}</h4>
        <p><strong>${item.original.answer}</strong></p>
        <p style="margin-top: 10px;">${item.original.text}</p>
      </div>
      <div class="story-block">
        <h4>${item.evidence.title}</h4>
        <p><strong>Error type:</strong> ${item.evidence.error.join(", ")}</p>
        <p><strong>Key frames:</strong> ${item.evidence.keyFrames.join(", ")}</p>
        <p><strong>Temporal markers:</strong> ${item.evidence.temporalMarkers.join("; ")}</p>
        <p style="margin-top: 10px;"><strong>Guidance:</strong> ${item.evidence.guidance}</p>
      </div>
      <div class="story-block">
        <h4>${item.corrected.title}</h4>
        <p><strong>${item.corrected.answer}</strong></p>
        <p style="margin-top: 10px;">${item.corrected.text}</p>
      </div>
    `;
  }

  function renderGuardrailCase(item) {
    document.getElementById("case-visual").innerHTML = `
      <div class="story-block" style="height: 100%;">
        <h4>Question type</h4>
        <p>${item.question}</p>
        <div class="guardrail-grid" style="margin-top: 18px;">
          <div class="guardrail-card bad">
            <strong>Unsafe patch</strong>
            <p style="margin-top: 8px;">${item.bad}</p>
          </div>
          <div class="guardrail-card good">
            <strong>Leakage-safe patch</strong>
            <p style="margin-top: 8px;">${item.good}</p>
          </div>
        </div>
      </div>
    `;

    document.getElementById("case-story").innerHTML = `
      <div class="story-block">
        <h4>Why the bad version fails</h4>
        <p>It makes the patch itself sufficient to infer the answer, so the student no longer needs to inspect the video.</p>
      </div>
      <div class="story-block">
        <h4>Why the safe version works</h4>
        <p>${item.takeaway}</p>
      </div>
      <div class="story-block">
        <h4>Design rule</h4>
        <p>${item.principle}</p>
      </div>
    `;
  }

  function renderCases() {
    renderCaseNav();
    const current = data.cases.find((item) => item.id === state.caseId);
    setText("case-tag", current.tag);
    setText("case-title", current.title);
    setText("case-principle", current.principle);
    if (current.kind === "pipeline") {
      renderPipelineCase(current);
    } else {
      renderGuardrailCase(current);
    }
  }

  function renderValidation() {
    const leakageBody = document.getElementById("leakage-body");
    leakageBody.innerHTML = "";
    data.results.leakage.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${row.label}</td><td>${formatValue(row.direct)}%</td><td>${formatValue(row.partial)}%</td><td>${formatValue(row.total)}%</td>`;
      leakageBody.appendChild(tr);
    });

    const stageRoot = document.getElementById("stage-grid");
    stageRoot.innerHTML = "";
    data.results.stages.forEach((stage) => {
      const card = document.createElement("div");
      card.className = "stage-card";
      card.innerHTML = `<strong>${stage.label}</strong><span>Intervention ratio: ${formatValue(stage.intervention)}%</span><span>Training accuracy: ${formatValue(stage.accuracy)}%</span>`;
      stageRoot.appendChild(card);
    });
  }

  function bindCopyButton() {
    const button = document.getElementById("copy-bibtex");
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(data.bibtex);
        button.textContent = "Copied";
        button.classList.add("is-copied");
        window.setTimeout(() => {
          button.textContent = "Copy BibTeX";
          button.classList.remove("is-copied");
        }, 1400);
      } catch (error) {
        button.textContent = "Copy failed";
      }
    });
  }

  function bindReveal() {
    const nodes = document.querySelectorAll(".reveal");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    nodes.forEach((node) => observer.observe(node));
  }

  renderHero();
  renderResults();
  renderCases();
  renderValidation();
  bindCopyButton();
  bindReveal();
})();
