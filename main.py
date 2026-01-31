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

app = FastAPI()


@app.post("/start")
def start(payload: dict):
    player = (payload.get("player", "") or "").strip()
    team = (payload.get("team", "") or "").strip()

    if not player or not team:
        return {"ok": False, "reason": "missing_player_or_team"}

    # Consentiamo l'asta SOLO se il giocatore è ancora svincolato
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

    # Rimuovi dagli svincolati il giocatore assegnato
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
    # Ritorna solo gli svincolati rimasti
    return {"players": sorted(AVAILABLE_PLAYERS)}


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

    # Restore: se hai cancellato una voce perché sbagliata,
    # rimetti il giocatore tra gli svincolati.
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
