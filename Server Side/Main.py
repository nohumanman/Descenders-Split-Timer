from flask import Flask, render_template, jsonify, request, make_response, redirect
from Player import Player
from Timer import Timer
import time
from PlayerDB import PlayerDB
from Tokens import webhook, bot_token
from RidersGate import RidersGate
from Boundry import Checkpoint


app = Flask(__name__)

timer = Timer()
riders_gate = RidersGate()

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
logging.basicConfig(
    filename="log.txt",
    filemode="a",
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S')

''' IN-Descenders API calls '''


def get_player_from_req(request) -> Player:
    steam_id = request.args.get("steam_id")
    steam_name = request.args.get("steam_name")
    world_name = request.args.get("world_name")
    return timer.get_player(steam_id, steam_name, world_name)

@app.route("/API/DESCENDERS/ON-BOUNDRY-ENTER/<boundry_guid>")
def on_boundry_enter(boundry_guid):
    player = get_player_from_req(request)
    trail_name = request.args.get("trail_name")
    client_time = request.args.get("client_time")
    logging.info(f'''Player {player.steam_name} (id {player.steam_id}) on {player.world} has entered boundry on trail "{trail_name}" with client time {client_time}''')
    player.trail = trail_name
    return player.on_boundry_enter(float(client_time))

@app.route("/API/DESCENDERS/ON-BOUNDRY-EXIT/<boundry_guid>")
def on_boundry_exit(boundry_guid):
    player = get_player_from_req(request)
    trail_name = request.args.get("trail_name")
    client_time = request.args.get("client_time")
    logging.info(f'''Player {player.steam_name} (id {player.steam_id}) on {player.world} has exited the boundry on trail "{trail_name}" with client time {client_time}''')
    player.trail = trail_name
    return player.on_boundry_exit(float(client_time))

@app.route("/API/DESCENDERS/ON-CHECKPOINT-ENTER/<checkpoint_num>")
def on_checkpoint_enter(checkpoint_num):
    player = get_player_from_req(request)
    client_time = request.args.get("client_time")
    trail_name = request.args.get("trail_name")
    total_checkpoints = request.args.get("total_checkpoints")
    checkpoint_type = request.args.get("checkpoint_type")
    logging.info(f'''Player {player.steam_name} (id {player.steam_id}) on {player.world} has entered a checkpoint on {trail_name} (Checkpoint {checkpoint_num}/{total_checkpoints} and type '{checkpoint_type}')''')
    checkpoint = Checkpoint(checkpoint_type, int(checkpoint_num), int(total_checkpoints))
    player.trail = trail_name
    return player.on_checkpoint_enter(checkpoint, client_time)

@app.route("/API/DESCENDERS/ON-DEATH")
def on_death():
    player = get_player_from_req(request)
    logging.info(f'''Player {player.steam_name} (id {player.steam_id}) on {player.world} has died.''')
    player.on_respawn()
    return "TIME INVALID; RESPAWNED"
    #return "valid"

@app.route("/API/DESCENDERS/ON-MAP-ENTER")
def on_map_enter():
    player = get_player_from_req(request)
    world_name = request.args.get("world_name")
    logging.info(f'''Player {player.steam_name} (id {player.steam_id}) on {player.world} has entered the map.''')
    player.on_map_enter(world_name)
    if (player.ban_status == "unbanned" or player.ban_status== "shadowban"):
        return "valid"
    else:
        return player.ban_status

@app.route("/API/DESCENDERS/ON-MAP-EXIT")
def on_map_exit():
    player = get_player_from_req(request)
    logging.info(f'''Player {player.steam_name} (id {player.steam_id}) on {player.world} has exited the world.''')
    player.on_map_exit()
    return "valid"

@app.route("/API/DESCENDERS/GET-BAN-STATUS")
def descenders_get_ban_status():
    player = get_player_from_req(request)
    logging.info(f'''Player {player.steam_name} (id {player.steam_id}) on {player.world} has retrieved ban status.''')
    if (player.ban_status == "unbanned" or player.ban_status== "shadowban"):
        return "valid"
    else:
        return player.ban_status


@app.route("/API/DESCENDERS/ON-BIKE-SWITCH")
def on_bike_switch():
    player = get_player_from_req(request)
    new_bike = request.args.get("new_bike")
    logging.info(f'''Player {player.steam_name} (id {player.steam_id}) on {player.world} has switched to bike {new_bike}''')
    return player.on_bike_switch(new_bike)
    

@app.route("/API/DESCENDERS/GET-RIDERS-GATE")
def get_riders_gate():
    player = get_player_from_req(request)
    #logging.info(f'''Player {player.steam_name} (id {player.steam_id}) on {player.world} has requested the gate status.''')
    return {
        "random_delay" : riders_gate.random_delay
    }



@app.route("/API/MONITOR/<steam_id>")
def app_monitor_steam_id(steam_id):
    name = request.cookies.get('id')
    if name == "4565421332145321234565tr5":
        if timer.players[steam_id] in timer.monitored_players:
            timer.monitored_players.remove(timer.players[steam_id])
            timer.players[steam_id].monitored = False
        else:
            timer.monitored_players.append(timer.players[steam_id])
            timer.players[steam_id].monitored = True
    return "Monitoring"

@app.route("/API/UPDATE-BAN-STATUS/<steam_id>")
def api_update_ban_status(steam_id):
    name = request.cookies.get('id')
    if name == "4565421332145321234565tr5":
        new_ban_status = request.args.get("ban_status")
        timer.players[steam_id].ban_status = new_ban_status
        PlayerDB.update_ban_status(steam_id, new_ban_status)
    return "complete"


@app.route("/API/BECOME-COMPETITOR/<steam_id>")
def api_become_competitor_toggle(steam_id):
    name = request.cookies.get('id')
    if name == "4565421332145321234565tr5":
        if timer.players[steam_id].is_competitor:
            PlayerDB.become_competitor(steam_id, False, timer.players[steam_id].steam_name)
            timer.players[steam_id].is_competitor = False
        else:
            PlayerDB.become_competitor(steam_id, True, timer.players[steam_id].steam_name)
            timer.players[steam_id].is_competitor = True
    return "Monitoring"

@app.route("/API/DASHBOARD/TRAILS")
def api_dashboard_trails():
    return jsonify({"data" : PlayerDB.get_trail_data()})

@app.route("/API/DASHBOARD/TRAIL-TIMESTAMPS/<trail_name>")
def api_dashboard_trail_timestamps(trail_name):
    return jsonify({"data": PlayerDB.get_times_trail_ridden(trail_name)})

@app.route("/API/DASHBOARD/GET-PLAYERS")
def api_get_players():
    try:
        return {
            "players":
                [
                    {
                        "steam_name": timer.players[player].steam_name,
                        "steam_id": str(timer.players[player].steam_id),
                        "current_world": timer.players[player].world,
                        "split_times": str(timer.players[player].trail_timer.times),
                        "is_competitor" : timer.players[player].is_competitor,
                        "online" : timer.players[player].online,
                        "colour" : (lambda online, is_competitor : "deep-purple accent-3" if (online and is_competitor) else("green accent-4" if (online) else("red accent-4")))(timer.players[player].online, timer.players[player].is_competitor),
                        "being_monitored" : (lambda player : True if (timer.players[player] in timer.monitored_players) else False)(player),
                        "current_trail" : timer.players[player].trail,
                        "ban_state" : timer.players[player].ban_status,
                        "current_bike" : timer.players[player].bike,
                        "total_time_on_world" : (lambda: PlayerDB.get_time_on_world(player, world=timer.players[player].world) if (timer.players[player].world != "none")  else "0")(),
                        "total_time" : PlayerDB.get_time_on_world(player),
                        "avatar_src": timer.players[player].avatar_src,
                    }
                    for player in timer.players
                ]
        }
    except Exception as e:
        print(e)

@app.route("/API/DESCENDERS-LEADERBOARD")
def api_descenders_leaderboard():
    try:
        num = int(request.args.get("num"))
    except:
        num = 10
    trail_name = request.args.get("trail_name")
    steam_name = request.args.get("steam_name")
    steam_id = request.args.get("steam_id")
    world_name = request.args.get("world_name")
    #logging.info(f'''Player {steam_name} (id {steam_id}) on {world_name} has requested leaderboard info.''')
    leaderboard_data = PlayerDB.get_leaderboard_descenders(trail_name, num=num)
    is_competitors = [data["is_competitor"] for data in leaderboard_data]
    steam_ids = [data["steam_id"] for data in leaderboard_data]
    steam_names = [data["steam_name"] for data in leaderboard_data]
    time_ids = [data["time_id"] for data in leaderboard_data]
    timestamps = [data["timestamp"] for data in leaderboard_data]
    total_times = [data["total_time"] for data in leaderboard_data]
    trail_names = [data["trail_name"] for data in leaderboard_data]
    was_monitoreds = [data["was_monitored"] for data in leaderboard_data]
    print("leaderboard fetch returned:" + str(leaderboard_data))
    return jsonify({
        "is_competitors" : is_competitors,
        "steam_ids" : steam_ids,
        "steam_names": steam_names,
        "time_ids": time_ids,
        "timestamps" : timestamps,
        "total_times": total_times,
        "trail_names": trail_names,
        "was_monitoreds": was_monitoreds
    })

@app.route("/API/DESCENDERS-GET-FASTEST-TIME")
def api_descenders_get_fastest_split_times():
    trail_name = request.args.get("trail_name")
    steam_id = request.args.get("steam_id")
    steam_name = request.args.get("steam_name")
    world_name = request.args.get("world_name")
    #logging.info(f'''Player {steam_name} (id {steam_id}) on {world_name} has requested split times of trail {trail_name}''')
    return {"fastest_split_times" : PlayerDB.get_fastest_split_times(trail_name, competitors_only=timer.competitors_only, min_timestamp=timer.timestamp, monitored_only=timer.monitored_only)}



@app.route("/API/TOGGLE-RIDERS-GATE-START")
def api_toggle_riders_gate_start():
    name = request.cookies.get('id')
    if name == "4565421332145321234565tr5":
        riders_gate.refresh_random_delay()
    return "Done"

def auto_gate():
    while True:
        riders_gate.refresh_random_delay()
        time.sleep(15)

import threading
threading.Thread(target=auto_gate).start()

@app.route("/API/GET-DATA/<index>")
def api_get_data(index):
    index = int(index)
    comp_only = request.args.get("competitor_only")
    timestamp = request.args.get("min_timestamp")
    monitored_only = request.args.get("monitored_only")
    if comp_only == "True":
        comp_only = True
    else:
        comp_only = False
    if monitored_only == "True":
        monitored_only = True
    else:
        monitored_only = False
    
    try:
        return jsonify({
            "time_start" : timer.monitored_players[index].trail_timer.time_started,
            "name" : timer.monitored_players[index].steam_name,
            "split_times" : timer.monitored_players[index].trail_timer.times,
            "fastest_split_times" : PlayerDB.get_fastest_split_times(timer.monitored_players[index].trail, competitors_only=comp_only, min_timestamp=timestamp, monitored_only=monitored_only),
            "entered_checkpoint" : True,#timer.monitored_players[index].has_entered_checkpoint,
            "monitoring" : True
        })
    except AttributeError as e:
        return jsonify({"monitoring" : False})


@app.route("/login-api", methods=["POST"])
def login():
    if request.method == "POST":
        user = request.form['password']
        if user == "Big Badonkas123":
            resp = make_response("200")
            resp.set_cookie('id', "4565421332145321234565tr5")
            return resp
        elif request.args.get("as_guest") == "true":
            resp = make_response("200")
            resp.set_cookie('isGuest', "true")
            return resp
        else:
            return "nope"


@app.route("/")
def dashboard():
    name = request.cookies.get('id')
    guest = request.cookies.get("isGuest")
    if name == "4565421332145321234565tr5" or guest == "true":
        return render_template("Dashboard.html")
    else:
        return render_template("Login.html")

@app.route("/Mobile")
def mobile():
    return render_template("Mobile.html")

@app.route("/GET-LOG-AS-LIST")
def get_log_as_string():
    with open("log.txt", "rt") as file:
        log_as_list = [x for x in file.read().split("\n")]
        log_as_list.reverse()
        return jsonify({"data" : log_as_list})

@app.route("/MONITOR")
def ui_monitor():
    return render_template("UI.html")

@app.route("/LOG")
def log_html():
    return render_template("Log.html")

if __name__ == "__main__":
	app.run(host="0.0.0.0", port="8443", ssl_context="adhoc", debug=True)
