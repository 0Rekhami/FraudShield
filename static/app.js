const API = "";  // Même domaine — FastAPI sert les fichiers statiques

let totalCount = 0, fraudCount = 0, alertCount = 0;
let riskCounts = { LOW: 0, MEDIUM: 0, HIGH: 0 };
const txHistory = [];

/* ── Navigation ── */
function showSection(name) {
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.getElementById("section-" + name).classList.add("active");
  event.currentTarget.classList.add("active");
}

/* ── API Health ── */
async function checkHealth() {
  const dot = document.getElementById("status-dot");
  const txt = document.getElementById("status-text");
  try {
    const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) {
      dot.className = "status-dot online";
      txt.textContent = "API connectée";
    } else throw new Error();
  } catch {
    dot.className = "status-dot offline";
    txt.textContent = "Mode simulation";
  }
}

/* ── Prediction ── */
async function runPrediction() {
  const btn = document.getElementById("btn-analyze");
  const label = document.getElementById("btn-label");
  const arrow = document.getElementById("btn-arrow");
  const spinner = document.getElementById("spinner");

  btn.disabled = true;
  label.textContent = "Analyse...";
  arrow.style.display = "none";
  spinner.style.display = "block";

  const payload = {
    amount:        parseFloat(document.getElementById("amount").value),
    hour:          parseInt(document.getElementById("hour").value),
    merchant_type: document.getElementById("merchant_type").value,
    country:       document.getElementById("country").value,
    tx_per_hour:   parseInt(document.getElementById("tx_per_hour").value),
    is_new_device: parseInt(document.getElementById("is_new_device").value),
    distance_km:   parseFloat(document.getElementById("distance_km").value),
  };

  try {
    const r = await fetch(`${API}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(5000)
    });
    if (!r.ok) throw new Error("API error");
    const data = await r.json();
    renderResult(data, payload);
  } catch {
    renderResult(simulate(payload), payload);
  } finally {
    btn.disabled = false;
    label.textContent = "Analyser";
    arrow.style.display = "block";
    spinner.style.display = "none";
  }
}

/* ── Simulation locale (si API down) ── */
function simulate(p) {
  let score = 0.05;
  if (p.merchant_type === "crypto")   score += 0.28;
  if (p.merchant_type === "transfer") score += 0.12;
  if (p.is_new_device === 1)          score += 0.20;
  if (p.tx_per_hour > 5)              score += 0.20;
  if (p.distance_km > 200)            score += 0.15;
  if (p.amount > 500)                 score += 0.10;
  if (p.hour < 5 || p.hour > 22)     score += 0.10;
  score = Math.min(score + (Math.random() - 0.3) * 0.1, 0.99);
  score = Math.max(score, 0.01);
  const isFraud = score > 0.50;
  const risk = score > 0.75 ? "HIGH" : score > 0.40 ? "MEDIUM" : "LOW";
  return {
    transaction_id: "SIM-" + Date.now(),
    is_fraud: isFraud,
    fraud_score: parseFloat(score.toFixed(4)),
    legit_score: parseFloat((1 - score).toFixed(4)),
    risk_level: risk,
    timestamp: new Date().toISOString(),
    alert_sent: isFraud && score > 0.50
  };
}

/* ── Render Result ── */
function renderResult(data, payload) {
  const panel = document.getElementById("result-panel");
  panel.style.display = "block";

  const pct = Math.round(data.fraud_score * 100);

  /* verdict */
  const verdict = document.getElementById("result-verdict");
  verdict.textContent = data.is_fraud ? "Fraude détectée" : "Transaction légitime";
  verdict.style.color = data.is_fraud ? "var(--danger)" : "var(--ok)";

  document.getElementById("result-id").textContent = data.transaction_id;

  /* badge */
  const badge = document.getElementById("risk-badge");
  badge.textContent = data.risk_level;
  badge.className = "risk-badge " + data.risk_level;

  /* score bar */
  document.getElementById("score-value").textContent = pct + "%";
  const fill = document.getElementById("score-fill");
  fill.style.width = pct + "%";
  fill.style.background = pct > 75 ? "var(--danger)" : pct > 40 ? "var(--warn)" : "var(--ok)";

  /* meta */
  document.getElementById("legit-val").textContent = Math.round(data.legit_score * 100) + "%";
  document.getElementById("alert-val").textContent = data.alert_sent ? "Oui" : "Non";
  document.getElementById("ts-val").textContent = new Date(data.timestamp).toLocaleTimeString("fr-FR");

  /* alert banner */
  document.getElementById("alert-banner").style.display = data.alert_sent ? "flex" : "none";

  /* counters */
  totalCount++;
  if (data.is_fraud) fraudCount++;
  if (data.alert_sent) alertCount++;
  riskCounts[data.risk_level]++;
  updateStats();

  /* history */
  txHistory.unshift({ ...data, amount: payload.amount, merchant: payload.merchant_type, country: payload.country });
  updateHistory();
}

/* ── Stats ── */
function updateStats() {
  document.getElementById("st-total").textContent  = totalCount;
  document.getElementById("st-fraud").textContent  = fraudCount;
  document.getElementById("st-rate").textContent   = totalCount ? (fraudCount / totalCount * 100).toFixed(1) + "%" : "—";
  document.getElementById("st-alerts").textContent = alertCount;

  const max = Math.max(...Object.values(riskCounts), 1);
  ["LOW", "MEDIUM", "HIGH"].forEach(r => {
    const key = r.toLowerCase().replace("ium", "").replace("ow", "ow");
    const barKey = r === "LOW" ? "low" : r === "MEDIUM" ? "med" : "high";
    document.getElementById("bar-" + barKey).style.width = (riskCounts[r] / max * 100) + "%";
    document.getElementById("cnt-" + barKey).textContent = riskCounts[r];
  });
}

/* ── History table ── */
function updateHistory() {
  const tbody = document.getElementById("tx-tbody");
  if (!txHistory.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-row">Aucune transaction analysée.</td></tr>';
    return;
  }
  tbody.innerHTML = txHistory.slice(0, 50).map(h => {
    const chip = h.is_fraud
      ? '<span class="verdict-chip fraud">FRAUDE</span>'
      : '<span class="verdict-chip legit">LÉGIT</span>';
    const pct = Math.round(h.fraud_score * 100);
    return `<tr>
      <td>${h.transaction_id.slice(-10)}</td>
      <td>${parseFloat(h.amount).toFixed(2)}</td>
      <td>${h.merchant}</td>
      <td>${h.country}</td>
      <td>${pct}%</td>
      <td>${chip}</td>
    </tr>`;
  }).join("");
}

/* ── Init ── */
checkHealth();
setInterval(checkHealth, 15000);
