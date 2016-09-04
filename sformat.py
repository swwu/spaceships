def neq_slashed(*args):
    if args[1:] == args[:-1]:
        return "%s" % args[0]
    else:
        return "/".join(("%s"%a for a in args))

# prints 1G instead of 1000000000, etc
def si_number(n):
    for base,suffix in [(1e12,"T"),(1e9,"G"),(1e6,"M"),(1e3,"k")]:
        if n >= base:
            return "%.3f%s" % (n/base, suffix)


