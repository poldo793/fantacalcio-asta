import threading
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import auction
from players import PLAYERS

ADMIN_TEAM = "Monkey D. United"

app = FastAPI()


@app.post("/start")
def start(payload: dict):
    player = payload.get("player", "")
    team = payload.get("team", "")
    ok = auction.start_auction(player, team)
    return {"ok": ok}


@app.post("/bid")
def bid(payload: dict):
    team = payload.get("team", "")
    ok = auction.place_bid(team)
    return {"ok": ok}


@app.get("/status")
def status():
    return auction.get_status()


@app.post("/confirm")
def confirm(payload: dict):
    team = payload.get("team", "")
    ok = auction.confirm(team, ADMIN_TEAM)
    return {"ok": ok}


@app.post("/cancel")
def cancel(payload: dict):
    team = payload.get("team", "")
    ok = auction.cancel(team, ADMIN_TEAM)
    return {"ok": ok}


@app.get("/players")
def players():
    return {"players": PLAYERS}


@app.get("/history")
def history():
    return {"history": auction.get_history()}


def _timer_loop():
    while True:
        auction.tick()
        time.sleep(0.2)


threading.Thread(target=_timer_loop, daemon=True).start()

app.mount("/", StaticFiles(directory="static", html=True), name="static")
