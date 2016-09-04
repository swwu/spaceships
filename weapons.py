import scales
import sformat

#1 1.5 2 3 4 6
#1 5

# converts 100 -> 2dx50
def dice_to_formatted(n,dmg_mult=1):
    mult = scales.get_closest_scale_value(n, [1,5])
    return "%sdx%s" % (n // mult, mult*dmg_mult)

class BaseWeapon:
    name = None
    dmg_dice_scale = None
    dmg_mult = 1
    dmg_kw = None
    armor_div = None
    rof = None

    def __init__(self, w_json):
        self.name = w_json["name"]
        self.dmg_dice_scale = scales.get_scale(
                "dmg_dice", 2, 1)
        self.dmg_mult = w_json["dmg_mult"]
        self.dmg_kw = w_json["dmg_kw"]
        self.armor_div = w_json["armor_div"]
        self.rof = w_json["rof"]

    def get_weap_data(self, sm):
        dmg_dice = self.dmg_dice_scale.get_scale_value(sm)
        return {"dmg_label":
                dice_to_formatted(
                    dmg_dice, self.dmg_mult),
                "size_label": "SM%s"%sm,
                "dmg_dice": dmg_dice,
                "dmg_kw": self.dmg_kw,
                "armor_div": self.armor_div,
                "rof": self.rof}

class BeamWeapon(BaseWeapon):
    size_name_scale = None
    def __init__(self, w_json):
        super().__init__(w_json)
        self.size_name_scale = scales.scale_from_json(
                w_json["size"])

    def get_weap_data(self,sm):
        return dict(super().get_weap_data(sm),
                **{"size_label":
                    "%sJ %s" % (
                        sformat.si_number(
                            self.size_name_scale.get_scale_value(sm)),
                        self.name)})

class MissileWeapon(BaseWeapon):
    pass

def weap_from_json(w_json):
    return {"beam": BeamWeapon,
            "missile": MissileWeapon
            }.get(w_json["type"])(w_json)




