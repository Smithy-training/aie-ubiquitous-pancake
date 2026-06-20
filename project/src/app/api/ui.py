from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard() -> HTMLResponse:
    return HTMLResponse(
        """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Pricing Service</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fb;
      --surface: #ffffff;
      --text: #18202a;
      --muted: #667085;
      --line: #d9dee7;
      --accent: #057a6f;
      --accent-strong: #045f57;
      --warn: #ad5f00;
      --danger: #b42318;
      --ok: #067647;
      --code: #101828;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family:
        Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 15px;
      letter-spacing: 0;
    }

    header {
      border-bottom: 1px solid var(--line);
      background: var(--surface);
    }

    .topbar {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 0;
    }

    h1 {
      margin: 0;
      font-size: 22px;
      line-height: 1.2;
      font-weight: 700;
    }

    .status-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }

    .pill {
      min-height: 30px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 10px;
      background: var(--surface);
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }

    .pill.ok {
      color: var(--ok);
      border-color: #a9d8c3;
    }

    .pill.warn {
      color: var(--warn);
      border-color: #f5c16c;
    }

    main {
      width: min(1180px, calc(100% - 32px));
      margin: 24px auto 40px;
      display: grid;
      grid-template-columns: minmax(320px, 430px) minmax(0, 1fr);
      gap: 20px;
      align-items: start;
    }

    section {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }

    h2 {
      margin: 0 0 14px;
      font-size: 16px;
      line-height: 1.3;
    }

    form {
      display: grid;
      gap: 14px;
    }

    label {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 13px;
    }

    input,
    select {
      width: 100%;
      height: 42px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      background: #fff;
      color: var(--text);
      font: inherit;
    }

    input:focus,
    select:focus {
      border-color: var(--accent);
      outline: 3px solid #c8eee9;
    }

    .split {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .toggle {
      height: 42px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      color: var(--text);
    }

    .toggle input {
      width: 18px;
      height: 18px;
      accent-color: var(--accent);
    }

    button,
    a.button {
      height: 42px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      border: 1px solid var(--accent);
      border-radius: 6px;
      padding: 0 14px;
      background: var(--accent);
      color: #fff;
      font: inherit;
      font-weight: 650;
      text-decoration: none;
      cursor: pointer;
    }

    button:hover,
    a.button:hover {
      background: var(--accent-strong);
      border-color: var(--accent-strong);
    }

    button.secondary,
    a.button.secondary {
      background: var(--surface);
      color: var(--accent);
    }

    .actions {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }

    .result-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }

    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-height: 92px;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }

    .metric strong {
      display: block;
      font-size: 24px;
      line-height: 1.15;
      overflow-wrap: anywhere;
    }

    pre {
      margin: 0;
      min-height: 260px;
      overflow: auto;
      border-radius: 8px;
      background: var(--code);
      color: #f7fafc;
      padding: 14px;
      font-size: 13px;
      line-height: 1.45;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .stack {
      display: grid;
      gap: 20px;
    }

    .links {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .history-list {
      display: grid;
      gap: 8px;
      max-height: 260px;
      overflow: auto;
    }

    .history-item {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      display: grid;
      gap: 4px;
      font-size: 13px;
    }

    .history-item strong {
      font-size: 14px;
    }

    .warning {
      display: none;
      margin: 0 0 16px;
      border: 1px solid #f5c16c;
      border-radius: 8px;
      padding: 10px 12px;
      color: var(--warn);
      background: #fff7e8;
    }

    .error {
      color: var(--danger);
    }

    @media (max-width: 860px) {
      .topbar {
        align-items: flex-start;
        flex-direction: column;
      }

      .status-row {
        justify-content: flex-start;
      }

      main {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 560px) {
      .split,
      .actions,
      .result-grid {
        grid-template-columns: 1fr;
      }

      section {
        padding: 14px;
      }
    }
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <h1>AI Pricing Service</h1>
      <div class="status-row">
        <span id="serviceStatus" class="pill">Service: checking</span>
        <span id="modelStatus" class="pill">Model: checking</span>
        <span id="modelMeta" class="pill">Version: unknown</span>
      </div>
    </div>
  </header>

  <main>
    <section>
      <h2>Prediction request</h2>
      <form id="predictForm">
        <label>
          Product ID
          <select id="productId" name="product_id">
            <option value="ELEC-100500">ELEC-100500</option>
            <option value="ELEC-200100">ELEC-200100</option>
            <option value="HOME-001200">HOME-001200</option>
            <option value="SPORT-420000">SPORT-420000</option>
            <option value="BOOK-777000">BOOK-777000</option>
          </select>
        </label>

        <div class="split">
          <label>
            Horizon days
            <input id="horizonDays" name="horizon_days" type="number" min="1" max="14" value="3" required>
          </label>
          <label>
            Base price
            <input
              id="basePrice"
              name="current_base_price"
              type="number"
              min="0.01"
              step="0.01"
              value="1500.00"
              required
            >
          </label>
        </div>

        <label class="toggle">
          Weekend
          <input id="isWeekend" name="is_weekend" type="checkbox" checked>
        </label>

        <div class="actions">
          <button type="submit">Run prediction</button>
          <button class="secondary" type="button" id="explainButton">Explain</button>
          <button class="secondary" type="button" id="resetButton">Reset</button>
        </div>
      </form>
    </section>

    <div class="stack">
      <section>
        <h2>Prediction result</h2>
        <p id="warning" class="warning"></p>
        <div class="result-grid">
          <div class="metric">
            <span>Demand units</span>
            <strong id="demandValue">-</strong>
          </div>
          <div class="metric">
            <span>Recommended price</span>
            <strong id="priceValue">-</strong>
          </div>
          <div class="metric">
            <span>Confidence</span>
            <strong id="confidenceValue">-</strong>
          </div>
        </div>
        <pre id="responseJson">{}</pre>
      </section>

      <section>
        <h2>Recent predictions</h2>
        <div id="historyList" class="history-list"></div>
      </section>

      <section>
        <h2>Service links</h2>
        <div class="links">
          <a class="button secondary" href="/docs">OpenAPI UI</a>
          <a class="button secondary" href="/health/ready">Readiness JSON</a>
          <a class="button secondary" href="/v1/model/info">Model info</a>
          <a class="button secondary" href="/version">Version</a>
          <a class="button secondary" href="/metrics">Prometheus metrics</a>
        </div>
      </section>

      <section>
        <h2>AI usage</h2>
        <p>
          The service uses a scikit-learn RandomForestRegressor to predict product demand.
          The recommended price is calculated by business logic that uses the model output.
        </p>
      </section>
    </div>
  </main>

  <script>
    const form = document.getElementById("predictForm");
    const warning = document.getElementById("warning");
    const responseJson = document.getElementById("responseJson");
    const demandValue = document.getElementById("demandValue");
    const priceValue = document.getElementById("priceValue");
    const confidenceValue = document.getElementById("confidenceValue");
    const historyList = document.getElementById("historyList");

    function setPill(id, text, mode) {
      const node = document.getElementById(id);
      node.textContent = text;
      node.classList.remove("ok", "warn");
      if (mode) {
        node.classList.add(mode);
      }
    }

    function showResponse(payload) {
      responseJson.textContent = JSON.stringify(payload, null, 2);
    }

    async function refreshStatus() {
      try {
        const health = await fetch("/health").then((response) => response.json());
        setPill("serviceStatus", `Service: ${health.status}`, "ok");
      } catch (error) {
        setPill("serviceStatus", "Service: unavailable", "warn");
      }

      try {
        const ready = await fetch("/health/ready").then((response) => response.json());
        if (ready.model_loaded) {
          setPill("modelStatus", "Model: ready", "ok");
          setPill("modelMeta", `${ready.metadata.model_type} ${ready.model_version}`, "ok");
        } else {
          setPill("modelStatus", "Model: not ready", "warn");
        }
      } catch (error) {
        setPill("modelStatus", "Model: not ready", "warn");
      }
    }

    async function runPrediction(event) {
      event.preventDefault();
      warning.style.display = "none";

      const payload = readPayload();

      try {
        const response = await fetch("/v1/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        showResponse(data);

        if (!response.ok) {
          demandValue.textContent = "-";
          priceValue.textContent = "-";
          confidenceValue.textContent = "-";
          responseJson.classList.add("error");
          return;
        }

        responseJson.classList.remove("error");
        demandValue.textContent = data.predicted_demand_units;
        priceValue.textContent = data.recommended_price.toLocaleString("ru-RU", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
        confidenceValue.textContent = `${Math.round(data.confidence_score * 100)}%`;

        if (data.warning) {
          warning.textContent = data.warning;
          warning.style.display = "block";
        }
        await refreshHistory();
      } catch (error) {
        showResponse({ error: String(error) });
        responseJson.classList.add("error");
      }
    }

    function readPayload() {
      return {
        product_id: document.getElementById("productId").value,
        horizon_days: Number(document.getElementById("horizonDays").value),
        current_base_price: Number(document.getElementById("basePrice").value),
        is_weekend: document.getElementById("isWeekend").checked,
      };
    }

    async function runExplain() {
      warning.style.display = "none";
      try {
        const response = await fetch("/v1/explain", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(readPayload()),
        });
        const data = await response.json();
        showResponse(data);
        responseJson.classList.toggle("error", !response.ok);
        await refreshHistory();
      } catch (error) {
        showResponse({ error: String(error) });
        responseJson.classList.add("error");
      }
    }

    async function refreshHistory() {
      try {
        const data = await fetch("/v1/predictions/recent").then((response) => response.json());
        const items = data.items.slice(0, 8);
        if (!items.length) {
          historyList.innerHTML = "<span class='pill'>No predictions yet</span>";
          return;
        }
        historyList.innerHTML = items.map((item) => `
          <div class="history-item">
            <strong>${item.product_id} · ${Math.round(item.confidence_score * 100)}%</strong>
            <span>Demand: ${item.predicted_demand_units}; Price: ${item.recommended_price}</span>
            <span>${item.request_id}</span>
          </div>
        `).join("");
      } catch (error) {
        historyList.innerHTML = "<span class='pill warn'>History unavailable</span>";
      }
    }

    form.addEventListener("submit", runPrediction);
    document.getElementById("explainButton").addEventListener("click", runExplain);
    document.getElementById("resetButton").addEventListener("click", () => {
      form.reset();
      demandValue.textContent = "-";
      priceValue.textContent = "-";
      confidenceValue.textContent = "-";
      warning.style.display = "none";
      responseJson.classList.remove("error");
      showResponse({});
    });

    refreshStatus();
    refreshHistory();
    form.dispatchEvent(new Event("submit"));
  </script>
</body>
</html>
        """
    )
