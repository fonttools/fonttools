"""
Conversion functions.
"""

# adapted from the UFO spec

def convertUFO1OrUFO2KerningToUFO3Kerning(kerning, groups):
    # Make lists of groups referenced in kerning pairs.
    firstReferencedGroups = set()
    secondReferencedGroups = set()
    for first, seconds in kerning.items():
        if first in groups:
            if not first.startswith("public.kern1."):
                firstReferencedGroups.add(first)
        for second in seconds.keys():
            if second in groups:
                if not second.startswith("public.kern2."):
                    secondReferencedGroups.add(second)
    # Create new names for these groups.
    firstRenamedGroups = {}
    for first in firstReferencedGroups:
        # Make a list of existing group names.
        existingGroupNames = groups.keys() + firstRenamedGroups.keys()
        # Add the prefix to the name.
        newName = "public.kern1." + first
        # Make a unique group name.
        newName = makeUniqueGroupName(newName, existingGroupNames)
        # Store for use later.
        firstRenamedGroups[first] = newName
    secondRenamedGroups = {}
    for second in secondReferencedGroups:
        # Make a list of existing group names.
        existingGroupNames = groups.keys() + secondRenamedGroups.keys()
        # Add the prefix to the name.
        newName = "public.kern2." + second
        # Make a unique group name.
        newName = makeUniqueGroupName(newName, existingGroupNames)
        # Store for use later.
        secondRenamedGroups[second] = newName
    # Populate the new group names into the kerning dictionary as needed.
    newKerning = {}
    for first, seconds in kerning.items():
        first = firstRenamedGroups.get(first, first)
        newSeconds = {}
        for second, value in seconds.items():
            second = secondRenamedGroups.get(second, second)
            newSeconds[second] = value
        newKerning[first] = newSeconds
    # Make copies of the referenced groups and store them
    # under the new names in the overall groups dictionary.
    allRenamedGroups = firstRenamedGroups.items()
    allRenamedGroups += secondRenamedGroups.items()
    for oldName, newName in allRenamedGroups:
        group = list(groups[oldName])
        groups[newName] = group
    # Return the kerning and the groups.
    return newKerning, groups, dict(side1=firstRenamedGroups, side2=secondRenamedGroups)

def findKnownKerningGroups(groups):
    """
    This will find kerning groups with known prefixes.
    These are the prefixes and sides that are handled:
    @MMK_L_ - side 1
    @MMK_R_ - side 2

    >>> testGroups = {
    ...     "@MMK_L_1" : None,
    ...     "@MMK_L_2" : None,
    ...     "@MMK_L_3" : None,
    ...     "@MMK_R_1" : None,
    ...     "@MMK_R_2" : None,
    ...     "@MMK_R_3" : None,
    ...     "@MMK_l_1" : None,
    ...     "@MMK_r_1" : None,
    ...     "@MMK_X_1" : None,
    ...     "foo" : None,
    ... }
    >>> first, second = findKnownKerningGroups(testGroups)
    >>> sorted(first)
    ['@MMK_L_1', '@MMK_L_2', '@MMK_L_3']
    >>> sorted(second)
    ['@MMK_R_1', '@MMK_R_2', '@MMK_R_3']
    """
    knownFirstGroupPrefixes = [
        "@MMK_L_"
    ]
    knownSecondGroupPrefixes = [
        "@MMK_R_"
    ]
    firstGroups = set()
    secondGroups = set()
    for groupName in groups.keys():
        for firstPrefix in knownFirstGroupPrefixes:
            if groupName.startswith(firstPrefix):
                firstGroups.add(groupName)
                break
        for secondPrefix in knownSecondGroupPrefixes:
            if groupName.startswith(secondPrefix):
                secondGroups.add(groupName)
                break
    return firstGroups, secondGroups


def makeUniqueGroupName(name, groupNames, counter=0):
    # Add a number to the name if the counter is higher than zero.
    newName = name
    if counter > 0:
        newName = "%s%d" % (newName, counter)
    # If the new name is in the existing group names, recurse.
    if newName in groupNames:
        return makeUniqueGroupName(name, groupNames, counter + 1)
    # Otherwise send back the new name.
    return newName

def test():
    """
    >>> testKerning = {
    ...     "A" : {
    ...         "A" : 1,
    ...         "B" : 2,
    ...         "CGroup" : 3,
    ...         "DGroup" : 4
    ...     },
    ...     "BGroup" : {
    ...         "A" : 5,
    ...         "B" : 6,
    ...         "CGroup" : 7,
    ...         "DGroup" : 8
    ...     },
    ...     "CGroup" : {
    ...         "A" : 9,
    ...         "B" : 10,
    ...         "CGroup" : 11,
    ...         "DGroup" : 12
    ...     },
    ... }
    >>> testGroups = {
    ...     "BGroup" : ["B"],
    ...     "CGroup" : ["C"],
    ...     "DGroup" : ["D"],
    ... }
    >>> kerning, groups, maps = convertUFO1OrUFO2KerningToUFO3Kerning(
    ...     testKerning, testGroups)
    >>> expected = {
    ...     "A" : {
    ...         "A": 1,
    ...         "B": 2,
    ...         "public.kern2.CGroup": 3,
    ...         "public.kern2.DGroup": 4
    ...     },
    ...     "public.kern1.BGroup": {
    ...         "A": 5,
    ...         "B": 6,
    ...         "public.kern2.CGroup": 7,
    ...         "public.kern2.DGroup": 8
    ...     },
    ...     "public.kern1.CGroup": {
    ...         "A": 9,
    ...         "B": 10,
    ...         "public.kern2.CGroup": 11,
    ...         "public.kern2.DGroup": 12
    ...     }
    ... }
    >>> kerning == expected
    True
    >>> expected = {
    ...     "BGroup": ["B"],
    ...     "CGroup": ["C"],
    ...     "DGroup": ["D"],
    ...     "public.kern1.BGroup": ["B"],
    ...     "public.kern1.CGroup": ["C"],
    ...     "public.kern2.CGroup": ["C"],
    ...     "public.kern2.DGroup": ["D"],
    ... }
    >>> groups == expected
    True
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
