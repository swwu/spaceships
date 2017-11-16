def neq_slashed(*args):
    if args[1:] == args[:-1]:
        return "%.0f" % args[0]
    else:
        return "/".join(("%.0f" % a for a in args))


def suffixed_number(n, suffixes):
    for base,suffix in suffixes:
        if n >= base:
            number_str = ("%.3f" % (n/base)).rstrip('0').rstrip('.')
            return "%s%s" % (number_str, suffix)

# prints 1G instead of 1000000000, etc
def si_number(n):
    return suffixed_number(n,
            [(1e12,"T"),(1e9,"G"),(1e6,"M"),(1e3,"k"),(1,"")])

# prints $1B instead of 1000000000, etc
def money_number(n):
    return "$%s" % suffixed_number(n,
            [(1e12,"T"),(1e9,"B"),(1e6,"M"),(1e3,"k"),(1,"")])

