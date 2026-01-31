import threading
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import auction
from players import PLAYERS

ADMIN_TEAM = "Monkey D. United"

# Lista svincolati "dinamica" in memoria:
# - quando confermi un'asta: rimuove il giocatore
# - se cancelli dallo storico: rimette il giocatore
AVAILABLE_PLAYERS = set(p.strip() for p in PLAYERS if p and p.strip())

ROLE_ORDER = {"POR": 0, "DIF": 1, "CEN": 2, "ATT": 3}


def extract_role(player_str: str) -> str:
    # Cerca l'ultima parentesi (ROLE) alla fine, es: "Audero - CRE (POR)"
    if not player_str:
        return ""
    s = player_str.strip()
    if s.endswith(")") and "(" in s:
        role = s[s.rfind("(") + 1 : -1].strip().upper()
        return role
    return ""


def extract_name(player_str: str) -> str:
    # Nome = parte prima di " - " (se presente), altrimenti stringa intera
    if not player_str:
        return ""
    s = player_str.strip()
    if " - " in s:
        return s.split(" - ", 1)[0].strip().lower()
    return s.lower()


def sort_players(players_iterable):
    # Ordina per: ruolo (POR/DIF/CEN/ATT) -> nome (alfabetico) -> fallback stringa
    def key_fn(s: str):
        role = extract_role(s)
        role_idx = ROLE_ORDER.get(role, 99)
        name = extract_name(s)
        return (role_idx, name, s.lower())

    return sorted(players_iterable, key=key_fn)


app = FastAPI()


@app.post("/start")
def start(payload: dict):
    player = (payload.get("player", "") or "").strip()
    team = (payload.get("team", "") or "").strip()

    if not player or not team:
        return {"ok": False, "reason": "missing_player_or_team"}

    # Asta SOLO se il giocatore è ancora svincolato
    if player not in AVAILABLE_PLAYERS:
        return {"ok": False, "reason": "player_not_available"}

    ok = auction.start_auction(player, team)
    return {"ok": ok}


@app.post("/bid")
def bid(payload: dict):
    team = (payload.get("team", "") or "").strip()
    inc = payload.get("inc", 1)

    if not team:
        return {"ok": False}

    ok = auction.place_bid(team, inc)
    return {"ok": ok}


@app.get("/status")
def status():
    return auction.get_status()


@app.post("/confirm")
def confirm(payload: dict):
    team = (payload.get("team", "") or "").strip()
    entry = auction.confirm(team, ADMIN_TEAM)

    if entry is None:
        return {"ok": False}

    # Rimuovi dagli svincolati il giocatore assegnato (stringa completa)
    player = (entry.get("player") or "").strip()
    if player:
        AVAILABLE_PLAYERS.discard(player)

    return {"ok": True, "entry": entry}


@app.post("/cancel")
def cancel(payload: dict):
    team = (payload.get("team", "") or "").strip()
    ok = auction.cancel(team, ADMIN_TEAM)
    return {"ok": ok}


@app.get("/players")
def players():
    # Ritorna svincolati ordinati: POR -> DIF -> CEN -> ATT, alfabetico dentro ogni gruppo
    return {"players": sort_players(AVAILABLE_PLAYERS)}


@app.get("/history")
def history():
    return {"history": auction.get_history()}


@app.post("/history/delete")
def history_delete(payload: dict):
    team = (payload.get("team", "") or "").strip()
    if team != ADMIN_TEAM:
        return {"ok": False}

    hid = payload.get("id")
    removed = auction.delete_history(hid)
    if removed is None:
        return {"ok": False}

    # Restore: rimetti il giocatore tra gli svincolati (stringa completa)
    player = (removed.get("player") or "").strip()
    if player:
        AVAILABLE_PLAYERS.add(player)

    return {"ok": True, "removed": removed}


def _timer_loop():
    while True:
        auction.tick()
        time.sleep(0.2)


threading.Thread(target=_timer_loop, daemon=True).start()

app.mount("/", StaticFiles(directory="static", html=True), name="static")
