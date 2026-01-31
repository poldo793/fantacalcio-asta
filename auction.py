import time
import threading

TIMER_SECONDS = 5

_state = {
    "active": False,
    "player": None,
    "leading_team": None,
    "highest_bid": 0,
    "timer_end": 0.0,
    "awaiting_confirmation": False,
}

_lock = threading.Lock()


def start_auction(player: str, team: str) -> bool:
    with _lock:
        # se siamo in conferma, non permettere restart
        if _state["awaiting_confirmation"]:
            return False

        _state["active"] = True
        _state["player"] = player.strip()
        _state["leading_team"] = team.strip()
        _state["highest_bid"] = 1
        _state["timer_end"] = time.time() + TIMER_SECONDS
        _state["awaiting_confirmation"] = False

    return True


def place_bid(team: str) -> bool:
    with _lock:
        if not _state["active"] or _state["awaiting_confirmation"]:
            return False

        _state["highest_bid"] += 1
        _state["leading_team"] = team.strip()
        _state["timer_end"] = time.time() + TIMER_SECONDS

    return True


def tick():
    with _lock:
        if not _state["active"] or _state["awaiting_confirmation"]:
            return

        if time.time() >= _state["timer_end"]:
            # stop offerte e chiedi conferma
            _state["active"] = False
            _state["awaiting_confirmation"] = True


def confirm(admin_team: str, expected_admin: str) -> bool:
    with _lock:
        if admin_team != expected_admin:
            return False
        if not _state["awaiting_confirmation"]:
            return False

        # qui in futuro: assegnazione + storico
        _state["awaiting_confirmation"] = False
        _state["player"] = None
        _state["leading_team"] = None
        _state["highest_bid"] = 0
        _state["timer_end"] = 0.0
        return True


def cancel(admin_team: str, expected_admin: str) -> bool:
    with _lock:
        if admin_team != expected_admin:
            return False
        if not _state["awaiting_confirmation"]:
            return False

        # reset e si può rifare
        _state["awaiting_confirmation"] = False
        _state["active"] = False
        _state["leading_team"] = None
        _state["highest_bid"] = 0
        _state["timer_end"] = 0.0
        return True


def get_status():
    with _lock:
        now = time.time()
        time_left = 0
        if _state["active"]:
            time_left = max(0, int(_state["timer_end"] - now))

        return {
            "active": _state["active"],
            "player": _state["player"],
            "leading_team": _state["leading_team"],
            "highest_bid": _state["highest_bid"],
            "time_left": time_left,
            "awaiting_confirmation": _state["awaiting_confirmation"],
        }
