#!/usr/bin/python3

import os
import sys
import dnf
import click
import pprint
from colorama import Fore, Back, Style


def splitFilename(filename):
    """
    Pass in a standard style rpm fullname

    Return a name, version, release, epoch, arch, e.g.::
        foo-1.0-1.i386.rpm returns foo, 1.0, 1, i386
        1:bar-9-123a.ia64.rpm returns bar, 9, 123a, 1, ia64

    Copied from rpmUtils.miscUtils in yum
    """

    if filename[-4:] == '.rpm':
        filename = filename[:-4]

    archIndex = filename.rfind('.')
    arch = filename[archIndex+1:]

    relIndex = filename[:archIndex].rfind('-')
    rel = filename[relIndex+1:archIndex]

    verIndex = filename[:relIndex].rfind('-')
    ver = filename[verIndex+1:relIndex]

    epochIndex = filename.find(':')
    if epochIndex == -1:
        epoch = ''
    else:
        epoch = filename[:epochIndex]

    name = filename[epochIndex + 1:verIndex]
    return name, ver, rel, epoch, arch


class NoSuchPackageException(Exception):
    """
    Exception class for requested packages that do not exist
    """
    def __init__(self, pkgname):
        Exception.__init__(self,
                           "Package name %s returned no packages" % pkgname)


class TooManyPackagesException(Exception):
    """
    Exception class for packages that appear multiple times in the repos
    """
    def __init__(self, pkgname):
        Exception.__init__(self,
                           "Too many packages returned for %s" % pkgname)


def setup_base_repo(use_system):
    """
    Enable only the official Fedora repositories

    Returns: dnf.Base containing all the package metadata from the standard
             repositories for binary RPMs
    """
    base = dnf.Base()
    base.read_all_repos()
    repo = base.repos.all()
    repo.disable()
    if use_system:
        repo = base.repos.get_matching("fedora")
        repo.enable()
        repo = base.repos.get_matching("updates")
        repo.enable()
    else:
        # Load the static data
        dir_path = os.path.dirname(os.path.realpath(__file__))
        repo_path = os.path.join(dir_path,
            "sampledata/repodata/fedora/linux/development/25/Everything/x86_64/os/")
        repo = base.repos.get_matching("fedora")
        repo.mirrorlist = None
        repo.metalink = None
        repo.baseurl = "file://" + repo_path
        repo.name = "static-binary"
        try:
            repo._id = "static-binary"
        except AttributeError:
            print("DNF 2.x required.", file=sys.stderr)
            sys.exit(1)
        repo.load()
        repo.enable()

    base.fill_sack(load_system_repo=False, load_available_repos=True)
    return base


def setup_source_repo(use_system):
    """
    Enable only the official Fedora source repositories

    Returns: dnf.Base containing all the package metadata from the standard
             repositories for SRPMs
    """
    base = dnf.Base()
    base.read_all_repos()
    repo = base.repos.all()
    repo.disable()
    if use_system:
        repo = base.repos.get_matching("fedora-source")
        repo.enable()
        repo = base.repos.get_matching("updates-source")
        repo.enable()
    else:
        # Load the static data
        dir_path = os.path.dirname(os.path.realpath(__file__))
        repo_path = os.path.join(dir_path,
            "sampledata/repodata/fedora/linux/development/25/Everything/source/tree/")
        repo = base.repos.get_matching("fedora-source")
        repo.mirrorlist = None
        repo.metalink = None
        repo.baseurl = "file://" + repo_path
        repo.name = "static-source"
        try:
            repo._id = "static-source"
        except AttributeError:
            print("DNF 2.x required.", file=sys.stderr)
            sys.exit(1)
        repo.load()
        repo.enable()

    base.fill_sack(load_system_repo=False, load_available_repos=True)
    return base


def get_query_objects(use_system):
    """
    Get query objects for binary packages and source packages

    Returns: tuple of (binary_query, sources_query)
    """
    binaries = setup_base_repo(use_system)
    sources = setup_source_repo(use_system)
    return (binaries.sack.query(), sources.sack.query())


def get_pkg_by_name(q, pkgname):
    """
    Try to find the package name as x86_64 and then noarch.
    This function will return exactly one result. If it finds zero or multiple
    packages that match the name, it will throw an error.
    """
    matched = q.filter(name=pkgname, latest=True, arch='x86_64')
    if len(matched) > 1:
        raise TooManyPackagesException(pkgname)

    if len(matched) == 1:
        # Exactly one package matched
        # Technically it's possible for there to also be a noarch package
        # with the same name, which is an edge case I'm not optimizing for
        # yet.
        return matched[0]

    matched = q.filter(name=pkgname, latest=True, arch='noarch')
    if len(matched) > 1:
        raise TooManyPackagesException(pkgname)

    if len(matched) == 1:
        # Exactly one package matched
        return matched[0]
    raise NoSuchPackageException(pkgname)


def get_srpm_for_package(source_query, pkg):
    # Get just the base name of the SRPM
    try:
        (sourcename, _, _, _, _) = splitFilename(pkg.sourcerpm)
    except Exception:
        print("Failure: %s(%s)" % (pkg.sourcerpm, pkg.name))
        raise

    matched = source_query.filter(name=sourcename, latest=True, arch='src')
    if len(matched) > 1:
        raise TooManyPackagesException(pkg.name)

    if len(matched) == 1:
        # Exactly one package matched
        return matched[0]

    raise NoSuchPackageException(pkg.name)


def get_srpm_for_package_name(binary_query, source_query, pkgname):
    """
    For a given package, retrieve a reference to its source RPM
    """
    pkg = get_pkg_by_name(binary_query, pkgname)

    return get_srpm_for_package(source_query, pkg)


def process_requirements(reqs, dependencies, ambiguities,
                         query, hints, pick_first,
                         follow_recommends):
    """
    Share code for recursing into requires or recommends
    """
    for require in reqs:
        required_packages = query.filter(provides=str(require), latest=True,
                                         arch='x86_64')

        # Check for noarch packages satisfying it
        if len(required_packages) == 0:
            required_packages = query.filter(provides=str(require), latest=True,
                                             arch='noarch')

        # If there are no dependencies, just return
        if len(required_packages) == 0:
            return

        # Check for multiple possible packages
        if len(required_packages) > 1:
            # Handle 'hints' list
            found = False
            for choice in hints:
                for rpkg in required_packages:
                    if rpkg.name == choice:
                        # This has been disambiguated; use this one
                        found = True
                        recurse_package_deps(rpkg,
                                             dependencies, ambiguities, query,
                                             hints, pick_first,
                                             follow_recommends)
                        break
                if found:
                    # Don't keep looking once we find a match
                    break

            if not found:
                if pick_first:
                    # First try to use something we've already discovered
                    for rpkg in required_packages:
                        if rpkg.name in dependencies:
                            return

                    # The user instructed processing to just take the first
                    # entry in the list.
                    for rpkg in required_packages:
                        if rpkg.arch == 'noarch' or rpkg.arch == 'x86_64':
                            recurse_package_deps(rpkg, dependencies,
                                                 ambiguities, query,
                                                 hints, pick_first,
                                                 follow_recommends)
                            break
                    continue
                # Packages not solved by 'hints' list
                # should be added to the ambiguities list
                unresolved = {}
                for rpkg in required_packages:
                    unresolved[rpkg.name] = rpkg
                ambiguities.append(unresolved)

            continue

        # Exactly one package matched, so proceed down into it.
        recurse_package_deps(required_packages[0],
                             dependencies, ambiguities, query,
                             hints, pick_first, follow_recommends)


def recurse_package_deps(pkg, dependencies, ambiguities,
                         query, hints, pick_first,
                         follow_recommends):
    """
    Recursively search through dependencies and add them to the list
    """
    if pkg.name in dependencies:
        # Don't recurse the same dependency twice
        return
    dependencies[pkg.name] = pkg

    # Process Requires:
    process_requirements(pkg.requires, dependencies, ambiguities, query, hints,
                         pick_first, follow_recommends)

    try:
        # Process Requires(pre|post)
        process_requirements(pkg.requires_pre, dependencies, ambiguities,
                             query, hints, pick_first, follow_recommends)
    except AttributeError:
        print("DNF 2.x required.", file=sys.stderr)
        sys.exit(1)

    if follow_recommends:
        process_requirements(pkg.recommends, dependencies, ambiguities, query,
                             hints, pick_first, follow_recommends)


def recurse_srpm_deps(source_pkg, dependencies, ambiguities, query, hints,
                      pick_first, follow_recommends):
    """
    Recursively search through dependencies and add them to the list
    """
    # Process Requires:
    # There is no BuildRecommends concept, so we don't
    # need to worry about that.
    process_requirements(source_pkg.requires, dependencies, ambiguities,
                         query, hints, pick_first, follow_recommends)


def recurse_build_deps(source_pkg, binaries, sources,
                       ambiguities,
                       binary_query, source_query,
                       hints, pick_first,
                       follow_recommends):
    """
    Recursively determine all build dependencies for this package
    """

    if source_pkg.name in sources:
        # Don't process the same Source RPM twice
        return

    sources[source_pkg.name] = source_pkg

    # Recursively get all of the Requires for building this
    # SRPM. There is no BuildRecommends concept, so we don't
    # need to worry about that.
    saved_binaries = binaries.copy()
    recurse_srpm_deps(source_pkg, binaries, ambiguities, binary_query,
                      hints, pick_first, follow_recommends)

    deplist = sorted(binaries, key=binaries.get)
    for dep in deplist:
        if dep in saved_binaries:
            # Don't needlessly recurse into binaries we've
            # already processed.
            continue

        if dep.startswith("_MULTI_:"):
            print("Skipping: %s (Use --hint to disambiguate)" % dep[8:])
            continue

        # Get the source RPM for this binary and recurse
        # into it.
        spkg = get_srpm_for_package(source_query, binaries[dep])
        recurse_build_deps(spkg, binaries, sources,
                           ambiguities,
                           binary_query, source_query,
                           hints, pick_first,
                           follow_recommends)


def print_package_name(pkgname, dependencies, full):
    """
    Parse the package name for the error state and
    print it with the correct verbosity.
    """

    printpkg = dependencies[pkgname]

    if full:
        print("%d:%s-%s-%s.%s" % (printpkg.epoch,
                                  printpkg.name,
                                  printpkg.version,
                                  printpkg.release,
                                  printpkg.arch))
    else:
        print(printpkg.name)


def resolve_ambiguity(dependencies, ambiguity):
    """
    Determine if any of the contents of an ambiguous lookup
    is already resolved by something in the dependencies.
    """
    for key in sorted(ambiguity, key=ambiguity.get):
        if key in dependencies:
            return True
    return False


@click.group()
def main():
    pass


@main.command(short_help="Get package dependencies")
@click.argument('pkgnames', nargs=-1)
@click.option('--hint', multiple=True,
              help="""
Specify a package to be selected when more than one package could satisfy a
dependency. This option may be specified multiple times.

For example, it is recommended to use --hint=glibc-minimal-langpack
""")
@click.option('--recommends/--no-recommends', default=True)
@click.option('--merge/--no-merge', default=False)
@click.option('--full-name/--no-full-name', default=False)
@click.option('--pick-first/--no-pick-first', default=False,
              help="""
If multiple packages could satisfy a dependency and no --hint package will
fulfill the requirement, automatically select one from the list.

Note: this result may differ between runs depending upon how the list is
sorted. It is recommended to use --hint instead, where practical.
""")
@click.option('--system/--no-system', default=False,
              help="If --system is specified, use the 'fedora', 'updates', "
                   "'source' and 'updates-source' repositories from the local "
                   "system configuration. Otherwise, use the static data from "
                   "the sampledata directory.")
def neededby(pkgnames, hint, recommends, merge, full_name, pick_first, system):
    """
    Look up the dependencies for each specified package and
    display them in a human-parseable format.
    """

    (binary_query, _) = get_query_objects(system)

    dependencies = {}
    ambiguities = []
    for pkgname in pkgnames:
        pkg = get_pkg_by_name(binary_query, pkgname)

        if not merge:
            # empty the dependencies list and start over
            dependencies = {}
            ambiguities = []

        recurse_package_deps(pkg, dependencies, ambiguities,
                             binary_query, hint, pick_first, recommends)

        # Check for unresolved deps in the list that are present in the
        # dependencies. This happens when one package has an ambiguous dep but
        # another package has an explicit dep on the same package.
        # This list comprehension just returns the set of dictionaries that
        # are not resolved by other entries
        ambiguities = [x for x in ambiguities
                       if not resolve_ambiguity(dependencies, x)]

        if not merge:
            # If we're printing individually, create a header
            print(Fore.GREEN + Back.BLACK + "=== %s.%s ===" % (
                pkg.name, pkg.arch) + Style.RESET_ALL)

            # Print just this package's dependencies
            for key in sorted(dependencies, key=dependencies.get):
                # Skip the initial package
                if key == pkgname:
                    continue
                print_package_name(key, dependencies, full_name)

            if len(ambiguities) > 0:
                print(Fore.RED + Back.BLACK + "=== Unresolved Requirements ===" +
                      Style.RESET_ALL)
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(ambiguities)

    if merge:
        # Print the complete set of dependencies together
        for key in sorted(dependencies, key=dependencies.get):
            print_package_name(key, dependencies, full_name)

        if len(ambiguities) > 0:
            print(Fore.RED + Back.BLACK + "=== Unresolved Requirements ===" +
                  Style.RESET_ALL)
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(ambiguities)


@main.command(short_help="Get Source RPM")
@click.argument('pkgnames', nargs=-1)
@click.option('--full-name/--no-full-name', default=False)
@click.option('--system/--no-system', default=False,
              help="If --system is specified, use the 'fedora', 'updates', "
                   "'source' and 'updates-source' repositories from the local "
                   "system configuration. Otherwise, use the static data from "
                   "the sampledata directory.")
def getsourcerpm(pkgnames, full_name, system):
    """
    Look up the SRPMs from which these binary RPMs were generated.

    This list will be displayed deduplicated and sorted.
    """
    (binary_query, source_query) = get_query_objects(system)

    srpm_names = {}
    for pkgname in pkgnames:
        pkg = get_srpm_for_package_name(binary_query, source_query, pkgname)

        srpm_names[pkg.name] = pkg

    for key in sorted(srpm_names, key=srpm_names.get):
        print_package_name(key, srpm_names, full_name)


@main.command(short_help="Get build dependencies")
@click.argument('pkgnames', nargs=-1)
@click.option('--hint', multiple=True,
              help="""
Specify a package to be selected when more than one package could satisfy a
dependency. This option may be specified multiple times.

For example, it is recommended to use --hint=glibc-minimal-langpack

For build dependencies, the default is to exclude Recommends: from the
dependencies of the BuildRequires.
""")
@click.option('--recommends/--no-recommends', default=False)
@click.option('--merge/--no-merge', default=False)
@click.option('--full-name/--no-full-name', default=False)
@click.option('--sources/--no-sources', default=True)
@click.option('--pick-first/--no-pick-first', default=False,
              help="""
If multiple packages could satisfy a dependency and no --hint package will
fulfill the requirement, automatically select one from the list.

Note: this result may differ between runs depending upon how the list is
sorted. It is recommended to use --hint instead, where practical.
""")
@click.option('--system/--no-system', default=False,
              help="If --system is specified, use the 'fedora', 'updates', "
                   "'source' and 'updates-source' repositories from the local "
                   "system configuration. Otherwise, use the static data from "
                   "the sampledata directory.")
def neededtoselfhost(pkgnames, hint, recommends, merge, full_name,
                     pick_first, sources, system):
    """
    Look up the build dependencies for each specified package
    and all of their dependencies, recursively and display them
    in a human-parseable format.
    """

    (binary_query, source_query) = get_query_objects(system)

    binary_pkgs = {}
    source_pkgs = {}
    ambiguities = []
    for pkgname in pkgnames:
        pkg = get_pkg_by_name(binary_query, pkgname)

        if not merge:
            binary_pkgs = {}
            source_pkgs = {}
            ambiguities = []

        # Get the source RPM for this package
        spkg = get_srpm_for_package(source_query, pkg)
        recurse_build_deps(spkg, binary_pkgs, source_pkgs,
                           ambiguities,
                           binary_query, source_query,
                           hint, pick_first, recommends)

        # Check for unresolved deps in the list that are present in the
        # dependencies. This happens when one package has an ambiguous dep but
        # another package has an explicit dep on the same package.
        # This list comprehension just returns the set of dictionaries that
        # are not resolved by other entries
        # We only search the binary packages here. This is a reduction; no
        # additional packages are discovered so we don't need to regenrate
        # the source RPM list.
        ambiguities = [x for x in ambiguities
                       if not resolve_ambiguity(binary_pkgs, x)]

        if not merge:
            # If we're printing individually, create a header
            print(Fore.GREEN + Back.BLACK + "=== %s.%s ===" % (
                pkg.name, pkg.arch) + Style.RESET_ALL)

            # Print just this package's dependencies
            if sources:
                for key in sorted(source_pkgs, key=source_pkgs.get):
                    # Skip the initial package
                    if key == pkgname:
                        continue
                    print_package_name(key, source_pkgs, full_name)
            else:
                for key in sorted(binary_pkgs, key=binary_pkgs.get):
                    # Skip the initial package
                    if key == pkgname:
                        continue
                    print_package_name(key, binary_pkgs, full_name)

            if len(ambiguities) > 0:
                print(Fore.RED + Back.BLACK +
                      "=== Unresolved Requirements ===" +
                      Style.RESET_ALL)
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(ambiguities)

    if merge:
        if sources:
            for key in sorted(source_pkgs, key=source_pkgs.get):
                print_package_name(key, source_pkgs, full_name)
        else:
            for key in sorted(binary_pkgs, key=binary_pkgs.get):
                print_package_name(key, binary_pkgs, full_name)
        if len(ambiguities) > 0:
            print(Fore.RED + Back.BLACK +
                  "=== Unresolved Requirements ===" +
                  Style.RESET_ALL)
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(ambiguities)

if __name__ == "__main__":
    main()
