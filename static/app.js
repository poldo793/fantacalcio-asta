async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });
  return res.json();
}

function setMsg(text) {
  const box = document.getElementById("msg");
  if (!box) return;
  box.innerText = text || "";
}

async function startAuction() {
  const player = document.getElementById("player").value.trim();
  const team = document.getElementById("team").value;
  if (!player || !team) return;

  const r = await postJson("/start", { player, team });

  if (!r.ok) {
    if (r.reason === "player_not_available") setMsg("Giocatore non disponibile (già assegnato o non in lista).");
    else if (r.reason === "insufficient_budget") setMsg(`Budget insufficiente: servono ${r.needed}, hai ${r.remaining}.`);
    else if (r.reason === "unknown_team") setMsg("Squadra non riconosciuta.");
    else setMsg("Impossibile avviare l’asta.");
  } else {
    setMsg("");
  }

  await refreshBudget();
}

async function bid(inc) {
  const team = document.getElementById("team").value;
  if (!team) return;

  const r = await postJson("/bid", { team, inc });

  if (!r.ok) {
    if (r.reason === "insufficient_budget") setMsg(`Budget insufficiente: per rilanciare servono ${r.needed}, hai ${r.remaining}.`);
    else if (r.reason === "auction_not_active") setMsg("Asta non attiva.");
    else setMsg("Rilancio non possibile.");
  } else {
    setMsg("");
  }

  await refreshBudget();
}

async function confirmWin() {
  const team = document.getElementById("team").value;
  const r = await postJson("/confirm", { team });

  if (!r.ok) {
    setMsg("Conferma non riuscita (solo admin).");
    return;
  }

  setMsg("");
  await refreshHistory();
  await loadPlayersDatalist();
  await refreshBudget();
}

async function cancelAuction() {
  const team = document.getElementById("team").value;
  await postJson("/cancel", { team });
}

async function deleteHistoryItem(id) {
  const team = document.getElementById("team").value;
  if (!team) return;

  const r = await postJson("/history/delete", { team, id });
  if (r.ok) {
    setMsg("");
    await refreshHistory();
    await loadPlayersDatalist();
    await refreshBudget();
  } else {
    setMsg("Eliminazione storico non riuscita (solo admin).");
  }
}

const TEAM_STORAGE_KEY = "fanta_team";

function loadTeam() {
  const saved = localStorage.getItem(TEAM_STORAGE_KEY);
  if (saved) {
    const sel = document.getElementById("team");
    if (sel) sel.value = saved;
  }
}

function saveTeam() {
  const sel = document.getElementById("team");
  const team = sel ? sel.value : "";
  if (team) localStorage.setItem(TEAM_STORAGE_KEY, team);
}

async function loadPlayersDatalist() {
  const res = await fetch("/players");
  const data = await res.json();

  const dl = document.getElementById("playersList");
  dl.innerHTML = "";

  (data.players || []).forEach(name => {
    const opt = document.createElement("option");
    opt.value = name;
    dl.appendChild(opt);
  });
}

function formatTs(ts) {
  try {
    const d = new Date(ts * 1000);
    return d.toLocaleString();
  } catch {
    return "";
  }
}

async function refreshHistory() {
  const box = document.getElementById("historyList");
  const res = await fetch("/history");
  const data = await res.json();
  const history = data.history || [];

  if (history.length === 0) {
    box.className = "muted";
    box.innerText = "Nessuna asta conclusa";
    return;
  }

  const myTeam = document.getElementById("team").value;
  const isAdmin = (myTeam === "Monkey D. United");

  box.className = "";
  box.innerHTML = "";

  history.forEach(item => {
    const row = document.createElement("div");
    row.className = "hist-item";

    const left = document.createElement("div");
    const when = item.ts ? ` <span class="muted">(${formatTs(item.ts)})</span>` : "";
    left.innerHTML = `<b>${item.player}</b> → ${item.winner} — <b>${item.price}</b>${when}`;

    row.appendChild(left);

    if (isAdmin && item.id) {
      const btn = document.createElement("button");
      btn.className = "danger";
      btn.textContent = "Elimina";
      btn.onclick = () => deleteHistoryItem(item.id);
      row.appendChild(btn);
    }

    box.appendChild(row);
  });
}

async function refreshBudget() {
  const team = document.getElementById("team").value;
  const out = document.getElementById("budgetRemaining");
  if (!out) return;

  if (!team) {
    out.innerText = "-";
    return;
  }

  const res = await fetch("/teams");
  const data = await res.json();

  const remaining = (data.remaining && data.remaining[team] !== undefined) ? data.remaining[team] : "-";
  out.innerText = remaining;
}

async function refresh() {
  const res = await fetch("/status");
  const s = await res.json();

  const view = document.getElementById("view");
  const timer = document.getElementById("timer");
  const admin = document.getElementById("admin");

  if (s.awaiting_confirmation) {
    view.innerText =
      `⏸ In attesa di conferma\n` +
      `Giocatore: ${s.player || "-"}\n` +
      `Offerta: ${s.highest_bid}\n` +
      `Leader: ${s.leading_team || "-"}`;
    timer.innerText = "";
  } else if (!s.active) {
    view.innerText = "Nessuna asta attiva";
    timer.innerText = "";
  } else {
    view.innerText =
      `Giocatore: ${s.player}\n` +
      `Offerta: ${s.highest_bid}\n` +
      `Leader: ${s.leading_team || "-"}`;
    timer.innerText = `⏱ Timer: ${s.time_left}s`;
  }

  const myTeam = document.getElementById("team").value;
  admin.style.display = (myTeam === "Monkey D. United" && s.awaiting_confirmation) ? "block" : "none";
}

document.addEventListener("DOMContentLoaded", () => {
  const teamSel = document.getElementById("team");
  if (teamSel) {
    loadTeam();
    teamSel.addEventListener("change", async () => {
      saveTeam();
      await refreshBudget();
      await refreshHistory();
    });
  }

  loadPlayersDatalist();
  refreshHistory();
  refreshBudget();

  setInterval(refresh, 300);
  setInterval(refreshHistory, 3000);
  setInterval(refreshBudget, 3000);
});
