import math
import numbers
import bisect
import sformat

def get_closest_tens_scale_indx(v, scale_cycle, bisect_right=False):
    tens = math.floor(math.log(v,10))
    base_v = v / (10 ** tens)
    if bisect_right:
        i = bisect.bisect_right(scale_cycle, base_v)
    else:
        i = bisect.bisect_left(scale_cycle, base_v)
    return tens,i

def get_smallest_larger_scale_value(v, scale_cycle):
    tens,i = get_closest_tens_scale_indx(v, scale_cycle, False)
    if i == len(scale_cycle):
        return 10 ** (tens+1)
    else:
        return scale_cycle[i] * (10 ** tens)

def get_largest_smaller_scale_value(v, scale_cycle):
    tens,i = get_closest_tens_scale_indx(v, scale_cycle, True)
    if i == 0:
        return scale_cycle[-1] * 10 ** (tens-1)
    else:
        return scale_cycle[i-1] * (10 ** tens)

class BaseScale:
    def to_markdown(self, min_sm=5, max_sm=15, is_money=False):
        sm_count = (max_sm - min_sm + 1)
        number_formatter = sformat.money_number if is_money else sformat.si_number
        lines = []
        lines.append("|SM|" + "".join((
            "%s|" % i for i in range(min_sm, max_sm+1))))
        lines.append("|-|" + "-|"*sm_count)
        lines.append("|#|" + "".join((
            "%s|" % number_formatter(self.get_scale_value(i))
            for i in range(min_sm, max_sm+1))))


        return "\n".join(lines)

    def get_scale_value(self, sm):
        return 0

class ConstantScale(BaseScale):
    val = 0
    def __init__(self, val):
        self.val = val

    def get_scale_value(self, sm):
        return self.val

class CycleScale(BaseScale):
    start_val = 1
    start_sm = 5

    cycle = None

    def __init__(self, start_val, start_sm, cycle):
        # doesn't really matter if it's smallest larger or largest smaller,
        # since we expect start_val to be directly a member of cycle
        self.start_val = get_smallest_larger_scale_value(start_val, DR_SCALE_CYCLE)
        self.start_sm = start_sm
        self.cycle = cycle

    def get_scale_value(self, sm):
        delta = sm - self.start_sm

        start_tens, start_scale_indx = get_closest_tens_scale_indx(
                self.start_val, self.cycle)
        scale_indx_raw = start_scale_indx + delta
        tens_mod, scale_indx = divmod(scale_indx_raw, len(self.cycle))

        return self.cycle[scale_indx] * (10 ** (start_tens + tens_mod))

class TruncatedCycleScale(CycleScale):
    min_sm = 0

    def __init__(self, start_val, start_sm, cycle, min_sm):
        super().__init__(start_val, start_sm, cycle)
        self.min_sm = min_sm

    def get_scale_value(self, sm):
        if sm < self.min_sm: return 0
        return super().get_scale_value(sm)


DR_SCALE_CYCLE = [1, 1.5, 2, 3, 5, 7]
class DRScale(CycleScale):
    def __init__(self, start_val, start_sm):
        super().__init__(start_val, start_sm, DR_SCALE_CYCLE)

DMG_DICE_SCALE_CYCLE = [1, 1.5, 2, 3, 4, 6]
class DmgDiceScale(CycleScale):
    def __init__(self, start_val, start_sm):
        super().__init__(start_val, start_sm, DMG_DICE_SCALE_CYCLE)

class Geometric10Scale(BaseScale):
    start_val = 1
    start_sm = 1

    def __init__(self, start_val, start_sm):
        self.start_val = start_val
        self.start_sm = start_sm

    def get_scale_value(self, sm):
        delta = sm - self.start_sm
        return start_val * (10 ** delta)

class Geometric10HalfScale(BaseScale):
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
    # if it's just a number then make it constant
    if isinstance(s_json, numbers.Number):
        return ConstantScale(s_json)

    scale_cycle = s_json["cycle"]
    start_val, start_sm = s_json["start"]
    min_sm = s_json.get("min_sm", 0)
    if isinstance(scale_cycle, str):
        return get_scale(scale_cycle, start_val, start_sm)
    else:
        # secretly everything is a TruncatedCycleScale
        return TruncatedCycleScale(start_val, start_sm, scale_cycle, min_sm)



