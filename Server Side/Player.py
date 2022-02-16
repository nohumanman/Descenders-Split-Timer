from posixpath import split
import time
from threading import Thread
import logging
import requests
from PlayerDB import PlayerDB
import threading
import random
from Tokens import webhook, steam_api_key
from TrailTimer import TrailTimer, AntiCheatMeasure, TimerNotStarted


class Player():
    def __init__(self, steam_name, steam_id, world_name, is_competitor, ban_status):
        print("Player created with steam id", steam_id)
        self.steam_name = steam_name
        self.steam_id = steam_id
        self.ban_status = ban_status
        self.world = world_name
        self.is_competitor = is_competitor
        self.monitored = False
        self.online = False
        self.time_started = 0
        self.trail_timer = TrailTimer(self)
        avatar_src_req = requests.get(
            f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_api_key}&steamids={steam_id}"
        )
        try:
            avatar_src = avatar_src_req.json()["response"]["players"][0]["avatarfull"]
            self.avatar_src = avatar_src
        except:
            self.avatar_src = ""
        self.times_entered = []
        self.times_exited = []
        self.trail = "unknown"
        self.bike = "unknown"
        self.update_player_in_db()

    def on_competitor_status_change(self, is_competitor):
        self.is_competitor = is_competitor
        self.update_player_in_db()

    def update_player_in_db(self):
        PlayerDB.update_player(self.steam_id, self.steam_name, self.is_competitor, self.avatar_src)

    def on_avatar_change(self, new_src):
        self.avatar_src = new_src
        self.update_player_in_db()

    def on_bike_switch(self, new_bike):
        self.bike = new_bike
        if self.bike == "roadbike":
            self.online = False
        return "valid"

    def on_boundry_enter(self, client_time : float):
        self.times_entered.append(client_time)
        return self.boundaries_are_valid()

    def on_boundry_exit(self, client_time : float):
        self.times_exited.append(client_time)
        return "valid"

    def boundaries_are_valid(self):
        boundries = []
        self.times_entered.sort()
        self.times_exited.sort()
        for enter in self.times_entered:
            boundries.append({"time" : enter, "type": "ENTER"})
        for exit in self.times_exited:
            boundries.append({"time" : exit, "type": "EXIT"})
        boundries.sort(key=lambda x: x['time'])
        amount_exits = 0
        amount_enters = 0
        for boundary in boundries:
            if boundary['type'] == "EXIT":
                amount_exits += 1
            elif boundary['type'] == "ENTER":
                amount_enters += 1
        logging.info(amount_exits)
        logging.info(amount_enters)
        if amount_exits+2 <= amount_enters:
            return "valid"
        return "OUT OF BOUNDS!"

    def on_checkpoint_enter(self, checkpoint, client_time):
        if checkpoint.type == "start":
            logging.info(f"Player {self.steam_name} has started trail!")
            self.trail_timer.start_timer(checkpoint)
        elif checkpoint.type == "intermediate":
            logging.info(f"Player {self.steam_name} has intermediate on trail!")
            try:
                logging.info("Taking Split Time")
                self.trail_timer.split(client_time)
            except AntiCheatMeasure:
                print("Anticheat activated!")
                logging.info("Anticheat activated!")
                return "ERROR: AntiCheatMeasure has been called."
            except TimerNotStarted:
                logging.info("Timer not started!")
                print("Timer not started!")
                return "ERROR: Timer Not Started!"
        elif checkpoint.type == "stop" and checkpoint.total_checkpoints == checkpoint.num+1:
            logging.info(f"Player {self.steam_name} has finished trail!")
            self.trail_timer.split(client_time)
            self.trail_timer.end_timer()
        print(f"total checkpoints: {checkpoint.total_checkpoints}")
        return "valid"

    def send_error(self, error):
        print(f"Sending error '{error}' to client!")

    def on_respawn(self):
        if self.trail_timer.started:
            self.trail_timer.cancel_timer()
            self.send_error("Time invalid: You Respawned")

    def on_map_enter(self, world_name):
        self.time_started = time.time()
        self.online = True
        self.world = world_name

    def on_map_exit(self):
        if (self.time_started != 0):
            self.online = False
            self.world = "unknown"
            self.trail_timer.cancel_timer()
            PlayerDB.end_session(
                self.steam_id,
                self.time_started,
                time.time(),
                self.world
            )
