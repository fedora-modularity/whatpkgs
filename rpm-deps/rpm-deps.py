__author__ = 'Stephen Gallagher'

import rpm
import operator

def recurse_deps(requiredict, ts, loopdetect, pkg):
    num_deps = 1; # This current level is a dep

    # Don't count the same requirement twice in one depchain
    if pkg in loopdetect:
        return 0
    loopdetect[pkg] = None

    #print("DEBUG: processing %s" % pkg)

    # Get the list of Requires from this package
    for requirement in requiredict[pkg]:
        # Convert each Requires into a package name
        # Get pkg satisfying req from Provides:
        mi = ts.dbMatch('provides', requirement)

        # If there's more than one package satisfying this Provides on the system,
        # treat it as both adding to the dep-chain
        for h in mi:
            #print("DEBUG: %s satisfies a dep for %s" % (h[rpm.RPMTAG_NAME], pkg))
            num_deps += recurse_deps(requiredict, ts, loopdetect, h[rpm.RPMTAG_NAME]);

    return num_deps

ts = rpm.TransactionSet()
mi = ts.dbMatch()

requiredict = {}
for h in mi:
    requiredict[h[rpm.RPMTAG_NAME]] = h[rpm.RPMTAG_REQUIRES]

depchains = {}

for pkg in requiredict.keys():
    loopdetect = {}
    depchains[pkg] = recurse_deps(requiredict, ts, loopdetect, pkg)

sortedchains = sorted(depchains.items(), key=operator.itemgetter(1))

for chain in sortedchains:
    print("%s: %d" % (chain[0], chain[1]))
