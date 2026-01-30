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
