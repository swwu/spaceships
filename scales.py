import math
import bisect

def get_closest_tens_scale_indx(v, scale_cycle):
    tens = math.floor(math.log(v,10))
    base_v = v / (10 ** tens)
    i = bisect.bisect_left(scale_cycle, base_v)
    return tens,i

def get_closest_scale_value(v, scale_cycle):
    tens,i = get_closest_tens_scale_indx(v, scale_cycle)
    if i == len(scale_cycle):
        return 10 ** (tens+1)
    else:
        return scale_cycle[i] * (10 ** tens)


class CycleScale:
    start_val = 1
    start_sm = 5

    cycle = None

    def __init__(self, start_val, start_sm, cycle):
        self.start_val = get_closest_scale_value(start_val, DR_SCALE_CYCLE)
        self.start_sm = start_sm
        self.cycle = cycle

    def get_scale_value(self, sm):
        delta = sm - self.start_sm

        start_tens, start_scale_indx = get_closest_tens_scale_indx(
                self.start_val, self.cycle)
        scale_indx_raw = start_scale_indx + delta
        tens_mod, scale_indx = divmod(scale_indx_raw, len(self.cycle))

        return self.cycle[scale_indx] * (10 ** (start_tens + tens_mod))

DR_SCALE_CYCLE = [1, 1.5, 2, 3, 5, 7]
class DRScale(CycleScale):
    def __init__(self, start_val, start_sm):
        super().__init__(start_val, start_sm, DR_SCALE_CYCLE)

DMG_DICE_SCALE_CYCLE = [1, 1.5, 2, 3, 4, 6]
class DmgDiceScale(CycleScale):
    def __init__(self, start_val, start_sm):
        super().__init__(start_val, start_sm, DMG_DICE_SCALE_CYCLE)

class Geometric10Scale:
    start_val = 1
    start_sm = 1

    def __init__(self, start_val, start_sm):
        self.start_val = start_val
        self.start_sm = start_sm

    def get_scale_value(self, sm):
        delta = sm - self.start_sm
        return start_val * (10 ** delta)

class Geometric10HalfScale:
    start_val = 1
    start_sm = 1

    def __init__(self, start_val, start_sm):
        self.start_val = start_val
        self.start_sm = start_sm

    def get_scale_value(self, sm):
        tens, odd = divmod(sm - self.start_sm, 2)
        return self.start_val * (10 ** tens) * (3 ** odd)


def get_scale(scale_type_name, start_val, start_sm):
    return {"dr": DRScale,
            "dmg_dice": DmgDiceScale,
            "geometric_10": Geometric10Scale,
            "geometric_10_half": Geometric10HalfScale
            }.get(scale_type_name, None)(start_val, start_sm)

def scale_from_json(s_json):
    return get_scale(s_json["type"],
            s_json["start"][0],
            s_json["start"][1])



