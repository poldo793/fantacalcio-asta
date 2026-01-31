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

const TEAM_STORAGE_KEY = "fanta_team";
const TEAM_LOCK_KEY = "fanta_team_locked";

// CAMBIA QUI IL CODICE (4 CIFRE)
const ADMIN_PIN = "1937";

function getSelectedTeam() {
  const sel = document.getElementById("team");
  return sel ? sel.value : "";
}

function loadTeam() {
  const saved = localStorage.getItem(TEAM_STORAGE_KEY);
  if (saved) {
    const sel = document.getElementById("team");
    if (sel) sel.value = saved;
  }
}

function lockTeamIfNeeded() {
  const sel = document.getElementById("team");
  if (!sel) return;

  const locked = localStorage.getItem(TEAM_LOCK_KEY) === "1";
  const hasTeam = !!sel.value;

  if (hasTeam && locked) sel.disabled = true;
  else sel.disabled = false;
}

function saveAndLockTeam() {
  const sel = document.getElementById("team");
  if (!sel) return;

  const team = sel.value;
  if (!team) return;

  localStorage.setItem(TEAM_STORAGE_KEY, team);

  // una volta scelto, blocca
  localStorage.setItem(TEAM_LOCK_KEY, "1");

  lockTeamIfNeeded();
}

function unlockTeamWithCode() {
  const codeEl = document.getElementById("adminCode");
  const code = (codeEl ? codeEl.value : "").trim();

  if (code.length !== 4 || !/^\d{4}$/.test(code)) {
    setMsg("Codice non valido: inserisci 4 cifre.");
    return;
  }

  if (code !== ADMIN_PIN) {
    setMsg("Codice admin errato.");
    return;
  }

  // Sblocca selezione
  localStorage.removeItem(TEAM_LOCK_KEY);

  const sel = document.getElementById("team");
  if (sel) sel.disabled = false;

  setMsg("Sbloccato. Ora puoi cambiare squadra e poi verrà ribloccata automaticamente.");

  // pulizia campo
  if (codeEl) codeEl.value = "";
}

async function startAuction() {
  const player = document.getElementById("player").value.trim();
  const team = getSelectedTeam();
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
  const team = getSelectedTeam();
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
  const team = getSelectedTeam();
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
  const team = getSelectedTeam();
  await postJson("/cancel", { team });
}

async function deleteHistoryItem(id) {
  const team = getSelectedTeam();
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

  // Elimina nello storico: resta legato all'admin vero (Monkey D. United) lato backend
  const myTeam = getSelectedTeam();
  const isAdminTeam = (myTeam === "Monkey D. United");

  box.className = "";
  box.innerHTML = "";

  history.forEach(item => {
    const row = document.createElement("div");
    row.className = "hist-item";

    const left = document.createElement("div");
    const when = item.ts ? ` <span class="muted">(${formatTs(item.ts)})</span>` : "";
    left.innerHTML = `<b>${item.player}</b> → ${item.winner} — <b>${item.price}</b>${when}`;

    row.appendChild(left);

    if (isAdminTeam && item.id) {
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
  const team = getSelectedTeam();
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
}

document.addEventListener("DOMContentLoaded", () => {
  const teamSel = document.getElementById("team");

  if (teamSel) {
    loadTeam();
    lockTeamIfNeeded();

    teamSel.addEventListener("change", async () => {
      saveAndLockTeam();
      await refreshBudget();
      await refreshHistory();
    });

    // se già settata, assicurati che sia locked
    if (teamSel.value) {
      localStorage.setItem(TEAM_LOCK_KEY, "1");
      lockTeamIfNeeded();
    }
  }

  loadPlayersDatalist();
  refreshHistory();
  refreshBudget();

  setInterval(refresh, 300);
  setInterval(refreshHistory, 3000);
  setInterval(refreshBudget, 3000);
});
