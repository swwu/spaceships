import scales
import sformat
import bisect

#1 1.5 2 3 4 6
#1 5

# generates multipliers for dmg_dice_to_formatted below. Multipliers are 1, 5, 10,
# 50, ...
def generate_mults(mult_cycle):
    tens = 0
    while True:
        for scale in mult_cycle:
            yield (10 ** tens) * scale
        tens += 1

class BaseWeapon:
    id = ""
    name = None
    dmg_track = 1
    dmg_kw = None
    armor_div = None
    rof = None
    draws_power = False

    def __init__(self, w_json):
        self.id = w_json["id"]
        self.name = w_json["name"]
        self.dmg_kw = w_json["dmg_kw"]
        self.armor_div = w_json["armor_div"]
        self.rof = w_json["rof"]
        self.draws_power = w_json["draws_power"]

    def get_weap_data(self, sm, is_turret):
        return {"type": "BASE TYPE PLEASE OVERRIDE",
                "dmg_label": "BASE VALUE PLEASE OVERRIDE",
                "size_label": "SM%s %s"%(sm, self.name),
                "dmg_kw": self.dmg_kw,
                "armor_div": self.armor_div,
                "rof": self.rof}



class BeamWeapon(BaseWeapon):
    # we use slightly modified ranges from the provided ones; in effect
    # treating all beam weapons as if they were 3 sizes smaller
    OFFSET_FACTOR = -3
    # these arrays start at SM-2 sized beams (3kJ)
    BEAM_HALF_RANGE_TRACKS = [
            [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,2,2,2,3,3,3,7,7,7,15],
            [0,0,0,0,0,0,0,0,0,1,1,1,2,2,2,3,3,3,7,7,7,15,15,15,30],
            [0,0,0,0,0,0,1,1,1,2,2,2,3,3,3,7,7,7,15,15,15,30,30,30,30],
            [0,0,0,1,1,1,2,2,2,3,3,3,7,7,7,15,15,15,30,30,30,70,70,70,150]
            ]
    BEAM_RANGE_TRACKS = [
            [0,0,0,0,0,0,1,1,1,1,1,1,2,2,2,5,5,5,10,10,10,20,20,20,50],
            [0,0,0,1,1,1,1,1,1,2,2,2,5,5,5,10,10,10,20,20,20,50,50,50,100],
            [0,0,0,1,1,1,2,2,2,5,5,5,10,10,10,20,20,20,50,50,50,100,100,100,100],
            [1,1,1,2,2,2,5,5,5,10,10,10,20,20,20,50,50,50,100,100,100,200,200,200,500]
            ]
    sacc = 0
    size_name_scale = scales.get_scale("geometric_10_half",1,-9)
    range_track = 0
    dmg_dice_scale = None
    def __init__(self, w_json):
        super().__init__(w_json)
        beam_json = w_json["beam"]
        self.sacc = beam_json["sacc"]
        self.range_track = beam_json["range_track"]
        self.dmg_dice_scale = scales.get_scale(
                "dmg_dice", 1, 1)

    def get_weap_data(self,sm,is_turret):
        dmg_dice = self.dmg_dice_scale.get_scale_value(sm)
        sacc = self.sacc

        size_str = "%sJ %s" % (
                sformat.si_number(
                    self.size_name_scale.get_scale_value(sm)), self.name)
        if is_turret:
            size_str = size_str + " Turret"
        else:
            size_str = "Fixed " + size_str
            sacc += 2

        return dict(super().get_weap_data(sm,is_turret),
                **{
                    "type": "beam",
                    "dmg_label":
                    "%s %s" % (
                        self.dmg_dice_to_formatted(dmg_dice),
                        self.dmg_kw),
                    "half_damage_range":
                    self.BEAM_HALF_RANGE_TRACKS[self.range_track][sm+2+self.OFFSET_FACTOR],
                    "range":
                    self.BEAM_RANGE_TRACKS[self.range_track][sm+2+self.OFFSET_FACTOR],
                    "sacc": sacc,
                    "size_label": size_str
                    })

    # converts 100 -> 2dx50, according to the Beam Damage and Range Table on SS p67
    def dmg_dice_to_formatted(self,n):
        if self.dmg_track == 1:
            DICE_NUMBERS = [2,3,4,6]
            MULT_NUMBERS = [1,5]
        elif self.dmg_track == 2:
            DICE_NUMBERS = [2,3,4,6,8]
            MULT_NUMBERS = [1,2,5]
        else:
            raise Exception("dmg_track must be 1 or 2")

        n *= self.dmg_track

        mult_generator = generate_mults(MULT_NUMBERS)
        mult = 0
        v = 0
        while True:
            mult = next(mult_generator)
            v = n // mult

            if v >= DICE_NUMBERS[0] and v <= DICE_NUMBERS[-1]:
                # it doesn't matter which way we bisect, we expect n to divide
                # "correctly"
                v = DICE_NUMBERS[bisect.bisect_left(DICE_NUMBERS, v)]
                break

        return "%sdx%s" % (v, mult*self.dmg_track)


class LauncherWeapon(BaseWeapon):
    # starts at SM-9
    # TODO: share with guns when those are implemented
    LAUNCHER_CALIBER_TRACK = [
            2,2.5,3,3.5,
            4,5,6,7,8,
            10,12,14,16,20,
            20,24,28,32,40,48,56,64,80,96,112]

    # what to multiply 6d by. starts at SM-9 as above
    WARHEAD_MULTIPLIER_TRACK = [
            5,6,7,8,
            10,12,15,18,20,
            25,30,35,40,50,
            60,70,80,100,120,140,160,200,240,280]

    big_name = "Bigger than 28cm launcher"
    speed = 0
    turns = 0

    def __init__(self, w_json):
        super().__init__(w_json)
        missile_json = w_json["missile"]
        self.speed = missile_json["speed"]
        self.turns = missile_json["turns"]
        self.big_name = missile_json["big_name"]

    def get_weap_data(self,sm,is_turret):
        sacc = 2 # TL10 - 8
        turns = self.turns
        name = self.name
        # launchers above 32cm get doubled lifetime (delta-v and thrust in
        # actual rules)
        if sm >= 8:
            sacc += 1
            turns *= 2
            name = self.big_name

        size_str = "%scm %s" % (
                self.LAUNCHER_CALIBER_TRACK[sm+9], self.name)
        if is_turret:
            size_str = size_str + " Turreted Launcher"
        else:
            size_str = size_str + " Tube"
            sacc += 2

        return dict(super().get_weap_data(sm,is_turret),
                **{
                    "type": "missile",
                    "dmg_label": "6dx%s" % self.WARHEAD_MULTIPLIER_TRACK[sm+9],
                    "range": self.speed * turns,
                    "sacc": sacc,
                    "size_label": size_str
                    })


def weap_from_json(w_json):
    return {"beam": BeamWeapon,
            "launcher": LauncherWeapon
            }.get(w_json["type"])(w_json)

