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

_history = []  # [{"id": 1, "player": "...", "winner": "...", "price": 10, "ts": 1700000000}]
_next_history_id = 1

_lock = threading.Lock()


def start_auction(player: str, team: str) -> bool:
    with _lock:
        if _state["awaiting_confirmation"]:
            return False

        _state["active"] = True
        _state["player"] = player.strip()
        _state["leading_team"] = team.strip()
        _state["highest_bid"] = 1
        _state["timer_end"] = time.time() + TIMER_SECONDS
        _state["awaiting_confirmation"] = False

    return True


def place_bid(team: str, inc: int = 1) -> bool:
    if inc is None:
        inc = 1
    try:
        inc = int(inc)
    except:
        inc = 1
    if inc <= 0:
        inc = 1

    with _lock:
        if not _state["active"] or _state["awaiting_confirmation"]:
            return False

        _state["highest_bid"] += inc
        _state["leading_team"] = team.strip()
        _state["timer_end"] = time.time() + TIMER_SECONDS

    return True


def tick():
    with _lock:
        if not _state["active"] or _state["awaiting_confirmation"]:
            return

        if time.time() >= _state["timer_end"]:
            _state["active"] = False
            _state["awaiting_confirmation"] = True


def confirm(admin_team: str, expected_admin: str) -> dict | None:
    """Ritorna l'entry storico creata, oppure None se non ok."""
    global _next_history_id

    with _lock:
        if admin_team != expected_admin:
            return None
        if not _state["awaiting_confirmation"]:
            return None

        entry = {
            "id": _next_history_id,
            "player": _state["player"],
            "winner": _state["leading_team"],
            "price": _state["highest_bid"],
            "ts": int(time.time()),
        }
        _next_history_id += 1
        _history.append(entry)

        # Reset dopo conferma
        _state["awaiting_confirmation"] = False
        _state["player"] = None
        _state["leading_team"] = None
        _state["highest_bid"] = 0
        _state["timer_end"] = 0.0

        return entry


def cancel(admin_team: str, expected_admin: str) -> bool:
    with _lock:
        if admin_team != expected_admin:
            return False
        if not _state["awaiting_confirmation"]:
            return False

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


def get_history():
    with _lock:
        return list(reversed(_history))


def delete_history(history_id: int) -> dict | None:
    """Elimina una voce storico per id e la ritorna (per eventuale restore svincolati)."""
    try:
        hid = int(history_id)
    except:
        return None

    with _lock:
        for i, item in enumerate(_history):
            if item.get("id") == hid:
                return _history.pop(i)
    return None
