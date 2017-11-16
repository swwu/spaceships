import collections

import systems
import scales
import sformat

SECTIONS_ORDER = ["front", "center", "rear"]
SYSTEMS_ORDER = ["1","2","3","4","5","6","core"]

SECTION_SCOPE_ALIASES = {
        "front": { "dr": "front_dr" },
        "center": { "dr": "center_dr" },
        "rear": { "dr": "rear_dr" }}

def add_values_dict(d1, d2, alias):
    for k2,v2 in d2.items():
        k1 = alias.get(k2,k2)
        if k1 in d1:
            d1[k1] += v2
        else:
            d1[k1] = v2

def mult_values_dict_scalar(d, n, alias):
    for k in d:
        d[k] *= n

def system_key_to_indx(key):
    if key == "core":
        return 7
    else:
        return int(key)

def indx_to_system_key(idx):
    if idx == 7:
        return "core"
    else:
        return "%.0f" % idx

class Ship:
    name = ""
    role = ""

    sm = 1

    # all values:
    # ht hnd sr lwt length front_dr center_dr rear_dr
    # thrust pp_draw pp_gen cost

    values = None

    # {"size": <number>, "section": <front|center|rear>, "location":
    # <1-7|core>, "count": <number>, "weapon": <weapon_id>}
    weapons = []

    # section -> location -> [weapon_idx, ...]
    # weapon_idx is index into weapons array
    weapon_mount_mapping = None

    # section -> location (1-6,core) -> part
    systems = {}

    def __init__(self, ship_json, all_systems, all_weapons):
        self.sm = ship_json["sm"]
        self.name = ship_json.get("name","")
        self.role = ship_json.get("role","")
        self.systems = ship_json["systems"]
        self.weapons = [
                {
                    "size": self.sm + w["rel_size"],
                    "section": w["section"],
                    "location": w["location"],
                    "count": w["count"],
                    "is_turret": w["is_turret"],
                    "weapon": w["weapon"]} for w in ship_json["weapons"]]
        self.reset_values(all_systems)

    # iterate all systems as ((section_key, system_key, system_sm), system)
    def iter_systems(self, all_systems):
        for section_key in SECTIONS_ORDER:
            section = self.systems[section_key]
            for system_key in SYSTEMS_ORDER:
                if system_key not in section: continue

                system_id_json = section[system_key]

                system_ids = []
                system_sm = self.sm
                if isinstance(system_id_json, list):
                    system_ids = system_id_json
                    system_sm -= 1
                else:
                    system_ids = [system_id_json]

                for system_id in system_ids:
                    system = all_systems[system_id]
                    yield ((section_key,system_key,system_sm),system)

    def iter_grouped_systems(self, all_systems):
        group_first_system_key = None
        group_last_system_key = None
        group_section_key = None
        group_system = None
        group_sm = None
        group_count = -1
        for ((section_key, system_key, system_sm),
                system) in self.iter_systems(all_systems):
            group_count += 1
            if (group_section_key != section_key or
                    group_system.s_id != system.s_id or
                    group_sm != system_sm):
                if group_section_key != None:
                    yield ((group_section_key,
                        (group_first_system_key, group_last_system_key),
                        group_sm, group_count), group_system)
                    group_count = 0
                group_first_system_key = system_key
                group_section_key = section_key
                group_sm = system_sm
                group_system = system
            group_last_system_key = system_key

        yield ((group_section_key,
            (group_first_system_key, group_last_system_key),
            group_sm, group_count+1), group_system)

    # Iterate all weapon mounts on ((section, size, count, is_turret), weapon)
    # where weapon is an object that inherits weapon.BaseWeapon. Empty mount
    # slots have weapon of None
    def iter_mounted_weapons(self, all_weapons):
        for section, section_info in self.weapon_mount_mapping.items():
            for location, weapon_idxs in section_info.items():
                for weapon_idx in weapon_idxs:
                    weapon_info = self.weapons[weapon_idx]
                    yield ((section,
                        weapon_info["size"],
                        weapon_info["count"],
                        weapon_info["is_turret"]),
                        all_weapons[weapon_info["weapon"]])

    def iter_grouped_mounted_weapons(self, all_weapons):
        # section -> size -> weapon_id -> is_turret -> count
        weapon_groupings = collections.defaultdict(
                lambda: collections.defaultdict(
                    lambda: collections.defaultdict(
                        lambda: collections.defaultdict(int))))
        for ((section, size, count, is_turret),
                weapon) in self.iter_mounted_weapons(all_weapons):
            weapon_groupings[section][size][weapon.id][is_turret] += count

        for section, section_info in weapon_groupings.items():
            for size, size_info in section_info.items():
                for weapon_idx, weapon_idx_info in size_info.items():
                    for is_turret, count in weapon_idx_info.items():
                        yield ((section,
                            size,
                            count,
                            is_turret),
                            all_weapons[weapon_idx])

    def reset_values(self, all_systems):
        self.values = {}
        self.weapon_mounts = collections.defaultdict(
                lambda: collections.defaultdict(int))
        self.calc_self_values()
        self.calc_systems_values(all_systems)
        self.calc_weapon_mountings(all_systems)

    def calc_self_values(self):
        sthp = scales.DRScale(20,5).get_scale_value(self.sm)
        self.values["st"] = self.values["hp"] = sthp
        ht = 13
        # TODO: also -1 ht if TL 7-9 and automation
        if self.sm <= 9:
            # TODO: technically only -1 if no engine room
            ht -= 1
        self.values["ht"] = ht
        self.values["hnd"] = -((self.sm - 4) // 3)
        self.values["sr"] = 4 if self.sm <= 6 else 5
        self.values["lwt"] = scales.Geometric10HalfScale(10,4).get_scale_value(self.sm)
        self.values["length"] = scales.DRScale(15,5).get_scale_value(self.sm)

    def calc_systems_values(self, all_systems):
        for ((section_key, system_key, system_sm),
                system) in self.iter_systems(all_systems):
            section_scope_alias = SECTION_SCOPE_ALIASES[section_key]
            add_values_dict(self.values,
                    system.get_values_delta(system_sm),
                    section_scope_alias)
            add_values_dict(self.weapon_mounts[section_key],
                    system.get_weapon_mounts(self.sm),
                    {})

    def calc_weapon_mountings(self, all_systems):
        self.weapon_mount_mapping = collections.defaultdict(
                lambda: collections.defaultdict(list))

        # section -> location -> size -> count
        weapon_mount_slots = collections.defaultdict(
                lambda: collections.defaultdict(
                    lambda: collections.defaultdict(int)))

        for ((section_key, system_key, system_sm),
                system) in self.iter_systems(all_systems):
            if not isinstance(system, systems.WeaponsBatterySystem):
                next
            weapon_mount_slots[section_key][system_key] = system.get_weapon_mounts(
                    system_sm)

        for weapon_idx,weapon in enumerate(self.weapons):
            section = weapon["section"]
            location = weapon["location"]
            size = weapon["size"]
            count = weapon["count"]

            if weapon_mount_slots[section][location][size] >= count:
                weapon_mount_slots[section][location][size] -= count
            else:
                raise Exception(
                        "Too many weapons of size %s mounted at %s %s" %
                        (size, section, location))

            self.weapon_mount_mapping[section][location].append(weapon_idx)


    def to_markdown(self, all_systems, all_weapons):
        lines = []

        lines.append("%s-class  " % self.name)
        lines.append("SM%s %s  " % (self.sm, self.role))
        lines.append("%sm" % self.values["length"])

        lines.append("\n")

        lines.append("| dST/HP | Hnd/SR | HT | Move | LWt | Load | SM | Occ | dDR | Range | Cost |")
        lines.append("|--------|--------|----|------|-----|------|----|-----|-----|-------|------|")
        lines.append("|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|" % (
            sformat.neq_slashed(self.values["st"],self.values["hp"]),
            "%s/%s" % (self.values["hnd"],self.values["sr"]),
            self.values["ht"],
            "%sG" % self.values["thrust"],
            sformat.si_number(self.values["lwt"]),
            "  ",# load , sformat.si_number(self.values["load"]),
            self.sm,
            "  ",# occ
            sformat.neq_slashed(self.values["front_dr"], self.values["center_dr"],
                self.values["rear_dr"]),
            "  ", #range
            sformat.money_number(self.values["cost"]) #cost
            ))

        lines.append("\n")
        lines.append("Weapons")
        lines.append("===")

        weapons_lines = collections.defaultdict(list)

        for ((weap_section, weap_size, weap_count, weap_is_turret), weap
                ) in self.iter_grouped_mounted_weapons(all_weapons):
            weapons_lines[weap_section].append(
                    ((weap_size, weap_count, weap_is_turret), weap))

        for section_lines in weapons_lines.values():
            section_lines.sort(key=lambda x: -x[0][0])


        for section_key in SECTIONS_ORDER:
            lines.append("\n")
            lines.append(section_key)
            lines.append("---")

            lines.append("| # | SM | Weapon | sAcc | Damage | Range | RoF | Rcl |")
            lines.append("|---|----|--------|------|--------|-------|-----|-----|")
            for ((weap_size, weap_count, weap_is_turret), weap) in weapons_lines[section_key]:
                size_str = "%s (%s)" % (weap_size, weap_size - self.sm)
                if weap == None:
                    lines.append("|%s|%s|%s|%s|%s|%s|%s|%s|" % (
                        weap_count, size_str, "No Weapon", "N/A", "N/A", "N/A", "N/A", "N/A"))
                else:
                    weap_data = weap.get_weap_data(weap_size, weap_is_turret)
                    range_str = None
                    if weap_data["type"] == "beam":
                        range_str = sformat.neq_slashed(weap_data["half_damage_range"], weap_data["range"])
                    else:
                        range_str = "%.0f" % weap_data["range"]

                    lines.append("|%s|%s|%s|%s|%s|%s|%s|%s|" % (
                        weap_count, # count
                        size_str, # size
                        weap_data["size_label"], # label
                        weap_data.get("sacc", "N/A"), # sAcc
                        weap_data["dmg_label"] + (" (%s)" % weap.armor_div)
                        if weap.armor_div != 1 else "", # dmg
                        range_str, # range
                        weap.rof, # rof
                        "" # rcl
                        ))


        lines.append("\n")
        lines.append("Systems")
        lines.append("===")

        systems_lines = collections.defaultdict(list)
        for ((section_key, (system_start_key, system_end_key), system_sm,
            num_systems), system) in self.iter_grouped_systems(all_systems):
            systems_lines[section_key].append(
                    (((system_start_key, system_end_key), system_sm,
                        num_systems), system))

        for section_key in SECTIONS_ORDER:
            lines.append("\n")
            lines.append(section_key)
            lines.append("---")
            for (((system_start_key, system_end_key), system_sm, num_systems),
                    system) in sorted(systems_lines[section_key],
                            key=lambda x: x[0][0]):

                system_key_label = None
                if system_start_key == system_end_key:
                    system_key_label = system_start_key
                else:
                    system_key_label = "%s-%s" % (
                        system_start_key,system_end_key)
                pp_draw = num_systems * system.pp_draw
                pp_gen = num_systems * system.get_values_delta(system_sm
                        ).get("pp_gen",0)

                system_detail_lines = []

                if system.volatile:
                    system_detail_lines.append(
                            "Volatile - roll vs HT if disabled, HT-5 if \
                            destroyed. Failure means the ship is explodes \
                            (reduced to -10xHP) at end of its next turn.")

                if isinstance(system, systems.WeaponsBatterySystem):
                    # size -> weapon_id -> is_turret -> count
                    mounted_weapons = collections.defaultdict(
                            lambda: collections.defaultdict(
                                lambda: collections.defaultdict(int)))
                    system_key_range = range(
                            system_key_to_indx(system_start_key),
                            system_key_to_indx(system_end_key)+1)
                    weapon_strs = []
                    for system_key_indx in system_key_range:
                        pp_draw_add = 0
                        location = indx_to_system_key(system_key_indx)
                        for weapon_idx in self.weapon_mount_mapping[
                                section_key][location]:
                            weapon_info = self.weapons[weapon_idx]
                            weapon = all_weapons[weapon_info["weapon"]]
                            if weapon.draws_power:
                                pp_draw_add = 1
                            weapon_strs.append(
                                    "%sx%s" % (
                                        weapon_info["count"],
                                        weapon.get_weap_data(
                                            weapon_info["size"],
                                            weapon_info["is_turret"])["size_label"]))
                        pp_draw += pp_draw_add
                    system_detail_lines.append("Mounted: %s" % ", ".join(weapon_strs))

                workspaces = system.get_values_delta(system_sm
                        ).get("workspaces",0) * num_systems
                if workspaces > 0:
                    system_detail_lines.append("%.0f workspaces" %
                            workspaces)

                system_detail_lines = ("\t - %s" % s for s in
                        system_detail_lines)

                system_key_label += "!" * pp_draw
                system_key_label += "+" * pp_gen

                range_size = system_key_to_indx(system_end_key) - \
                        system_key_to_indx(system_start_key) + 1

                name_str = system.name

                if range_size != num_systems:
                    name_str += " x%s" % num_systems


                lines.append("* [%s] %s" % (system_key_label, name_str))
                lines += system_detail_lines

        return "\n".join(lines)
