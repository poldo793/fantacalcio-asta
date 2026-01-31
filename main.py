from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from auction import start_auction, place_bid, get_status

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.post("/start/{player}/{team}")
def start(player: str, team: str):
    ok = start_auction(player, team)
    return {"started": ok}


@app.post("/bid")
def bid():
    ok = place_bid()
    return {"bid": ok}


@app.get("/status")
def status():
    return get_status()


