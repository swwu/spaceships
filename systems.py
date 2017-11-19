import collections
import math

import scales
import sformat

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

    def details_to_markdown_lines(self, sm, num_systems=1):
        lines = []

        workspaces = self.get_workspaces(sm) * num_systems
        if workspaces > 0:
            lines.append("%.0f workspaces" % workspaces)

        if self.volatile:
            lines.append("Volatile - roll vs HT if disabled, HT-5 if " +
                         "destroyed. Failure means the ship is explodes " +
                         "(reduced to -10xHP) at end of its next turn.")

        return lines

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
    hardened = False

    def __init__(self, comp_json):
        super().__init__(comp_json)
        armor_json = comp_json["armor"]
        self.dr_scale = scales.scale_from_json(armor_json["dr"])
        self.hardened = armor_json.get("hardened", False)

    def get_values_delta(self,sm):
        return dict(super().get_values_delta(sm),
                **{"dr": self.dr_scale.get_scale_value(sm)})

    def details_to_markdown_lines(self, sm, num_systems=1):
        lines = super().details_to_markdown_lines(sm)
        if self.hardened:
            lines.append("Hardened - reduce armor divisor by one step along (5, 3, 2, 1).")
        return lines

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

class HangarSystem(BaseSystem):
    capacity_scale = scales.TruncatedCycleScale(1, 5, [1, 3], 5)
    # for SM 5 and 6 launch rate = capacity
    launch_rate_scale = scales.TruncatedCycleScale(7, 10, [1, 2, 5], 7)

    def details_to_markdown_lines(self, sm, num_systems=1):
        values = self.get_values_delta(sm)

        lines = super().details_to_markdown_lines(sm)
        lines.append("Capacity: %sT" %
                sformat.si_number(values["hangar_capacity"] * num_systems))
        # extra adjacent hangars increase capacity but shouldn't increase
        # launch rate. It doing so here is a houserule
        lines.append("Launch Rate: %sT per minute" %
                sformat.si_number(values["launch_rate"] * num_systems))
        return lines

    def get_values_delta(self,sm):
        capacity = self.capacity_scale.get_scale_value(sm)
        launch_rate = capacity
        if sm >= 7:
            launch_rate = self.launch_rate_scale.get_scale_value(sm)
        return dict(super().get_values_delta(sm),
                **{"launch_rate": launch_rate,
                    "hangar_capacity": capacity
                    })

class CargoSystem(BaseSystem):
    capacity_scale = scales.CycleScale(1, 5, [1.5, 5])

    def details_to_markdown_lines(self, sm, num_systems=1):
        values = self.get_values_delta(sm)

        lines = super().details_to_markdown_lines(sm)
        lines.append("Capacity: %sT" %
                sformat.si_number(values["cargo_capacity"] * num_systems))
        return lines

    def get_values_delta(self,sm):
        capacity = self.capacity_scale.get_scale_value(sm)
        return dict(super().get_values_delta(sm),
                **{"cargo_capacity": capacity})

class FuelSystem(BaseSystem):
    capacity_scale = scales.CycleScale(1.5, 5, [1.5, 5])

    def details_to_markdown_lines(self, sm, num_systems=1):
        values = self.get_values_delta(sm)

        lines = super().details_to_markdown_lines(sm)
        lines.append("Fuel Capacity: %sT" %
                sformat.si_number(values["fuel_capacity"] * num_systems))
        return lines

    def get_values_delta(self,sm):
        capacity = self.capacity_scale.get_scale_value(sm)
        return dict(super().get_values_delta(sm),
                **{"fuel_capacity": capacity})

class ShieldSystem(BaseSystem):
    dr_scale = None

    def __init__(self, comp_json):
        shield_json = comp_json["shield"]
        self.dr_scale = scales.scale_from_json(shield_json["dr"])
        super().__init__(comp_json)

    def details_to_markdown_lines(self, sm, num_systems=1):
        values = self.get_values_delta(sm)

        lines = super().details_to_markdown_lines(sm)
        lines.append("Shield dDR: %s" % values["shield_dr"])
        lines.append("Shield dHP: %s" % values["shield_hp"])
        return lines

    def get_values_delta(self,sm):
        # Houserule: we model shields as objects with (non-ablative) DR equal
        # to a much smaller shield's DR and HP equal to a much larger shield's
        # DR
        shield_dr = self.dr_scale.get_scale_value(sm - 2)
        shield_hp = self.dr_scale.get_scale_value(sm + 2)
        return dict(super().get_values_delta(sm),
                **{"shield_dr": shield_dr,
                    "shield_hp": shield_hp})




class FabSystem(BaseSystem):

    def get_values_delta(self,sm):
        return dict(super().get_values_delta(sm),
                **{"ht": 1})



def system_from_json(comp_json):
    return {"armor": ArmorSystem,
            "weapons_battery": WeaponsBatterySystem,
            "power_plant": PowerPlantSystem,
            "engine": EngineSystem,
            "hangar": HangarSystem,
            "cargo": CargoSystem,
            "fuel": FuelSystem,
            "shield": ShieldSystem,
            "fab": FabSystem,
            "misc": BaseSystem
            }.get(comp_json["type"])(comp_json)



