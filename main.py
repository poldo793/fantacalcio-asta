import threading
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import auction
from players import PLAYERS

ADMIN_TEAM = "Monkey D. United"

# === BUDGET INIZIALI (come da te) ===
TEAM_BUDGETS = {
    "Monkey D. United": 215,
    "AC Ciughina": 148,
    "ASD Vetriolo": 0,
    "Atletico Carogna": 203,
    "Atletico Zio Porcone": 225,
    "DIRE91 Team": 0,
    "La Passione di Kristovic": 165,
    "PSD Paris San Donato": 180,
}

# Crediti residui (in memoria)
TEAM_REMAINING = dict(TEAM_BUDGETS)

# Lista svincolati "dinamica" in memoria:
# - quando confermi un'asta: rimuove il giocatore
# - se cancelli dallo storico: rimette il giocatore
AVAILABLE_PLAYERS = set(p.strip() for p in PLAYERS if p and p.strip())

ROLE_ORDER = {"POR": 0, "DIF": 1, "CEN": 2, "ATT": 3}


def extract_role(player_str: str) -> str:
    if not player_str:
        return ""
    s = player_str.strip()
    if s.endswith(")") and "(" in s:
        role = s[s.rfind("(") + 1 : -1].strip().upper()
        return role
    return ""


def extract_name(player_str: str) -> str:
    if not player_str:
        return ""
    s = player_str.strip()
    if " - " in s:
        return s.split(" - ", 1)[0].strip().lower()
    return s.lower()


def sort_players(players_iterable):
    def key_fn(s: str):
        role = extract_role(s)
        role_idx = ROLE_ORDER.get(role, 99)
        name = extract_name(s)
        return (role_idx, name, s.lower())

    return sorted(players_iterable, key=key_fn)


def get_remaining(team: str) -> int:
    return int(TEAM_REMAINING.get(team, 0))


def clamp_inc(inc) -> int:
    try:
        v = int(inc)
    except:
        v = 1
    if v <= 0:
        v = 1
    return v


app = FastAPI()


@app.get("/teams")
def teams():
    # Per UI (residui/budget)
    return {"budgets": TEAM_BUDGETS, "remaining": TEAM_REMAINING}


@app.post("/start")
def start(payload: dict):
    player = (payload.get("player", "") or "").strip()
    team = (payload.get("team", "") or "").strip()

    if not player or not team:
        return {"ok": False, "reason": "missing_player_or_team"}

    if team not in TEAM_BUDGETS:
        return {"ok": False, "reason": "unknown_team"}

    # Asta SOLO se il giocatore è ancora svincolato
    if player not in AVAILABLE_PLAYERS:
        return {"ok": False, "reason": "player_not_available"}

    # Prezzo iniziale sempre 1: controllo crediti
    if get_remaining(team) < 1:
        return {"ok": False, "reason": "insufficient_budget", "needed": 1, "remaining": get_remaining(team)}

    ok = auction.start_auction(player, team)
    return {"ok": ok}


@app.post("/bid")
def bid(payload: dict):
    team = (payload.get("team", "") or "").strip()
    inc = clamp_inc(payload.get("inc", 1))

    if not team:
        return {"ok": False, "reason": "missing_team"}

    if team not in TEAM_BUDGETS:
        return {"ok": False, "reason": "unknown_team"}

    # Serve conoscere il prezzo corrente per verificare il nuovo prezzo
    st = auction.get_status()
    if not st.get("active", False) or st.get("awaiting_confirmation", False):
        return {"ok": False, "reason": "auction_not_active"}

    current_price = int(st.get("highest_bid", 0))
    new_price = current_price + inc

    if get_remaining(team) < new_price:
        return {
            "ok": False,
            "reason": "insufficient_budget",
            "needed": new_price,
            "remaining": get_remaining(team),
        }

    ok = auction.place_bid(team, inc)
    return {"ok": ok}


@app.get("/status")
def status():
    return auction.get_status()


@app.post("/confirm")
def confirm(payload: dict):
    team = (payload.get("team", "") or "").strip()

    # conferma solo admin
    entry = auction.confirm(team, ADMIN_TEAM)
    if entry is None:
        return {"ok": False}

    player = (entry.get("player") or "").strip()
    winner = (entry.get("winner") or "").strip()
    price = int(entry.get("price") or 0)

    # Rimuovi il giocatore dagli svincolati
    if player:
        AVAILABLE_PLAYERS.discard(player)

    # Scala budget al vincitore (se esiste)
    if winner in TEAM_REMAINING:
        TEAM_REMAINING[winner] = max(0, int(TEAM_REMAINING[winner]) - price)

    return {"ok": True, "entry": entry, "remaining": TEAM_REMAINING}


@app.post("/cancel")
def cancel(payload: dict):
    team = (payload.get("team", "") or "").strip()
    ok = auction.cancel(team, ADMIN_TEAM)
    return {"ok": ok}


@app.get("/players")
def players():
    # svincolati ordinati: POR -> DIF -> CEN -> ATT, alfabetico dentro ogni gruppo
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

    # Restore giocatore tra gli svincolati
    player = (removed.get("player") or "").strip()
    if player:
        AVAILABLE_PLAYERS.add(player)

    # Refund budget al winner
    winner = (removed.get("winner") or "").strip()
    price = int(removed.get("price") or 0)
    if winner in TEAM_REMAINING:
        TEAM_REMAINING[winner] = int(TEAM_REMAINING[winner]) + price

    return {"ok": True, "removed": removed, "remaining": TEAM_REMAINING}


def _timer_loop():
    while True:
        auction.tick()
        time.sleep(0.2)


threading.Thread(target=_timer_loop, daemon=True).start()

app.mount("/", StaticFiles(directory="static", html=True), name="static")
