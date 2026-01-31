import time

current_player = None
current_bid = 0
current_team = None
timer_end = None
awaiting_confirmation = False

def start_auction(player, team):
    global current_player, current_bid, current_team, timer_end, awaiting_confirmation
    current_player = player
    current_team = team
    current_bid = 1
    timer_end = time.time() + 5
    awaiting_confirmation = False

def raise_bid(team):
    global current_bid, current_team, timer_end
    current_bid += 1
    current_team = team
    timer_end = time.time() + 5
import time
import threading

auction_state = {
    "active": False,
    "player": None,
    "team": None,
    "highest_bid": 0,
    "time_left": 0
}

TIMER_SECONDS = 5


def start_auction(player, team):
    if auction_state["active"]:
        return False

    auction_state["active"] = True
    auction_state["player"] = player
    auction_state["team"] = team
    auction_state["highest_bid"] = 1
    auction_state["time_left"] = TIMER_SECONDS

    threading.Thread(target=_run_timer, daemon=True).start()
    return True


def _run_timer():
    while auction_state["time_left"] > 0:
        time.sleep(1)
        auction_state["time_left"] -= 1

    auction_state["active"] = False


def place_bid():
    if not auction_state["active"]:
        return False

    auction_state["highest_bid"] += 1
    auction_state["time_left"] = TIMER_SECONDS
    return True


def get_status():
    return auction_state

