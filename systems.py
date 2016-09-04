import collections
import math

import scales

class BaseSystem:
    name = None
    s_id = None
    pp_draw = 0

    def __init__(self, comp_json):
        self.name = comp_json["name"]
        self.s_id = comp_json["id"]
        self.pp_draw = comp_json.get("pp_draw",0)

    def get_values_delta(self,sm):
        return {}

    def get_weapon_mounts(self,sm):
        return collections.defaultdict(int)

    def get_desc_text(self,sm):
        return ""

class ArmorSystem(BaseSystem):
    dr_scale = None

    def __init__(self, comp_json):
        super().__init__(comp_json)
        dr_json = comp_json["dr"]
        self.dr_scale = scales.get_scale(
                dr_json["type"],
                dr_json["start"][0],
                dr_json["start"][1])

    def get_values_delta(self,sm):
        return dict(super().get_values_delta(sm),
                **{"dr": self.dr_scale.get_scale_value(sm)})

class WeaponsBatterySystem(BaseSystem):
    mounts_json = None

    def __init__(self, comp_json):
        super().__init__(comp_json)
        self.mounts_json = comp_json["mounts"]

    def get_weapon_mounts(self,sm):
        mounts_by_size = collections.defaultdict(int)

        for size_mod_str,count in self.mounts_json.items():
            size_mod = int(size_mod_str)
            mounts_by_size[sm+size_mod] += count
        return mounts_by_size

class PowerPlantSystem(BaseSystem):
    pp_gen = 0
    def __init__(self, comp_json):
        super().__init__(comp_json)
        self.pp_gen = comp_json["pp_gen"]

    def get_values_delta(self,sm):
        return dict(super().get_values_delta(sm),
                **{"pp_gen": self.pp_gen})

class EngineSystem(BaseSystem):
    thrust = 0
    def __init__(self, comp_json):
        super().__init__(comp_json)
        self.thrust = comp_json["thrust"]

    def get_values_delta(self,sm):
        return dict(super().get_values_delta(sm),
                **{"thrust": self.thrust,
                   "hdn": math.floor(math.log(self.thrust,10))})

class FabSystem(BaseSystem):

    def get_values_delta(self,sm):
        return dict(super().get_values_delta(sm),
                **{"ht": 1})



def system_from_json(comp_json):
    return {"armor": ArmorSystem,
            "weapons_battery": WeaponsBatterySystem,
            "power_plant": PowerPlantSystem,
            "engine": EngineSystem,
            "fab": FabSystem,
            "misc": BaseSystem
            }.get(comp_json["type"])(comp_json)



