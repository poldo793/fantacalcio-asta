from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import auction

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return HTMLResponse(open("static/index.html").read())

@app.post("/start/{player}/{team}")
def start(player: str, team: str):
    auction.start_auction(player, team)
    return {"status": "started", "player": player}

@app.post("/bid/{team}")
def bid(team: str):
    auction.raise_bid(team)
    return {"bid": auction.current_bid, "team": team}
