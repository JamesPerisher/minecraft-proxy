import time
from threading import Thread

import os

ignore_list = ["entity_relative_move",
"entity_head_look",
"entity_metadata",
"time_update",
"entity_velocity",
"sound_effect",
"multi_block_change",
"entity_look_and_relative_move",
"entity_status",
"entity_teleport",
"block_change",
"spawn_mob",
"entity_look",
"entity_properties",
"spawn_object",
"destroy_entities",
"set_slot",
"chunk_data",
"keep_alive",
"join_game",
"plugin_message",
"server_difficulty",
"player_abilities",
"held_item_change",
"unlock_recipes",
"update_block_entity",
"spawn_experience_orb",
"player_position_and_look",
"world_border",
"spawn_position",
"window_items",
"entity_equipment",
"update_block_entity",
"update_health",
"spawn_player"]


global p
p = []

class cbuff:
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data

class playback_loop(Thread):
    def __init__(self, bridge, packets):
        super().__init__()
        self.bridge = bridge
        self.packets = packets

        self.running = False

    def run(self):
        self.running = True
        for i in self.packets:
            if not self.running:
                return
            if i[0] > 0:
                time.sleep(i[0])

            print(i)
            self.bridge.downstream.send_packet(i[1], i[2])

    def kill(self):
        self.running = False




def handle(bridge, buff, direction, name):
    # if name in ignore_list:
    #     return

    if direction == "downstream":
        if name in ["player_info", "player_list_item", "player_list_header_footer", "chat_message"]:
            buff.save()
            bridge.packets.append((time.time(), name, buff.read()))
            buff.restore()



def read_file(bridge, file):
    global p
    cached_packets_raw = []
    cached_packets = []

    try:
        with open(file, "r") as f:
            for i in f.readlines():
                time, name, data = i.split(" || ")

                time = float(time.strip())
                name = name.strip()
                data = eval(data.strip())

                cached_packets_raw.append((time, name, data))


    except FileNotFoundError:
        return "§c!File not found files: %s"%os.listdir()

    except ValueError:
        return "§c!Invalid file format"

    except Exception as e:
        return "§c!Error: %s: %s"%(str(type(e)), str(e))

    for i,j in enumerate(cached_packets_raw):
        j = ((cached_packets_raw[i-1][0] - j[0]) * -1, j[1], j[2])
        cached_packets.append(j)

    a = playback_loop(bridge, cached_packets)

    p.append(a)
    a.start()

    print("Reloaded")

    return "§a!Begining data playback"

def reload():
    global p
    for i in p:
        i.kill()
