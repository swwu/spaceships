import collections
import math

import scales

class BaseSystem:
    id = ""
    name = None
    s_id = None
    pp_draw = 0
    cost_scale = None
    workspace_scale = 0
    volatile = False

    def __init__(self, comp_json):
        self.id = comp_json["id"]
        self.name = comp_json["name"]
        self.s_id = comp_json["id"]
        self.pp_draw = comp_json.get("pp_draw",0)
        self.cost_scale = scales.scale_from_json(comp_json["cost"])
        self.workspace_scale = scales.scale_from_json(comp_json["workspaces"])
        self.volatile = comp_json.get("volatile", False)

    def get_values_delta(self,sm):
        return {"pp_draw": self.pp_draw,
                "cost": self.get_cost(sm),
                "workspaces": self.get_workspaces(sm)}

    def get_weapon_mounts(self,sm):
        return collections.defaultdict(int)

    def get_desc_text(self,sm):
        return ""

    def get_cost(self, sm):
        return self.cost_scale.get_scale_value(sm)

    def get_workspaces(self, sm):
        return self.workspace_scale.get_scale_value(sm)

    def to_markdown(self):
        lines = []
        lines.append(self.name)
        lines.append("===")
        lines.append("\n")
        lines.append("Workspaces")
        lines.append("---")
        lines.append(self.workspace_scale.to_markdown())
        lines.append("Cost")
        lines.append("---")
        lines.append(self.cost_scale.to_markdown(is_money=True))

        return "\n".join(lines)


class ArmorSystem(BaseSystem):
    dr_scale = None

    def __init__(self, comp_json):
        super().__init__(comp_json)
        armor_json = comp_json["armor"]
        self.dr_scale = scales.scale_from_json(armor_json["dr"])

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
        self.pp_gen = comp_json["power_plant"]["pp_gen"]
        super().__init__(comp_json)

    def get_values_delta(self,sm):
        return dict(super().get_values_delta(sm),
                **{"pp_gen": self.pp_gen})

class EngineSystem(BaseSystem):
    thrust = 0
    def __init__(self, comp_json):
        super().__init__(comp_json)
        engine_json = comp_json["engine"]
        self.thrust = engine_json["thrust"]

    def get_values_delta(self,sm):
        return dict(super().get_values_delta(sm),
                **{"thrust": self.thrust,
                   "hnd": math.floor(math.log(self.thrust,10))})

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



