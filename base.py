import json

import ships
import systems
import weapons


def load_ship(filename, all_systems, all_weapons):
    with open(filename, 'r') as infile:
        ship_json = json.load(infile)
    ship = ships.Ship(ship_json, all_systems, all_weapons)
    return ship

def load_systems(filename):
    with open(filename, 'r') as infile:
        systems_json = json.load(infile)
        comps = {}
        for comp_json in systems_json:
            if "id" not in comp_json: continue
            comp_id = comp_json["id"]
            comps[comp_id] = systems.system_from_json(comp_json)
        return comps

def load_weapons(filename):
    with open(filename, 'r') as infile:
        weaps_json = json.load(infile)
        comps = {}
        for comp_json in weaps_json:
            if "id" not in comp_json: continue
            comp_id = comp_json["id"]
            comps[comp_id] = weapons.weap_from_json(comp_json)
        return comps

all_systems = load_systems("data/json/systems.json")
all_weapons = load_weapons("data/json/weapons.json")
#ship = load_ship("data/json/int_peregrine.json", all_systems, all_weapons)
#ship = load_ship("data/json/ca_rubicon.json", all_systems, all_weapons)
ship = load_ship("data/json/bc_valorous.json", all_systems, all_weapons)

print(ship.to_markdown(all_systems, all_weapons))

#print(all_systems["hangar_bay"].to_markdown())

