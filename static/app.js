async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });
  return res.json();
}

async function startAuction() {
  const player = document.getElementById("player").value.trim();
  const team = document.getElementById("team").value;
  if (!player || !team) return;
  await postJson("/start", { player, team });
}

async function bid() {
  const team = document.getElementById("team").value;
  if (!team) return;
  await postJson("/bid", { team });
}

async function confirmWin() {
  const team = document.getElementById("team").value;
  await postJson("/confirm", { team });
}

async function cancelAuction() {
  const team = document.getElementById("team").value;
  await postJson("/cancel", { team });
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
    teamSel.addEventListener("change", saveTeam);
  }

  loadPlayersDatalist();
  setInterval(refresh, 300);
});
