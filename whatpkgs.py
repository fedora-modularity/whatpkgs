import sys
import dnf
import click
from rpmUtils.miscutils import splitFilename
from colorama import Fore, Back, Style


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


def setup_base_repo():
    """
    Enable only the official Fedora repositories

    Returns: dnf.Base containing all the package metadata from the standard
             repositories for binary RPMs
    """
    base = dnf.Base()
    base.read_all_repos()
    r = base.repos.all()
    r.disable()
    r = base.repos.get_matching("fedora")
    r.enable()
    r = base.repos.get_matching("updates")
    r.enable()

    base.fill_sack(load_system_repo=False, load_available_repos=True)
    return base


def setup_source_repo():
    """
    Enable only the official Fedora source repositories

    Returns: dnf.Base containing all the package metadata from the standard
             repositories for SRPMs
    """
    base = dnf.Base()
    base.read_all_repos()
    r = base.repos.all()
    r.disable()
    r = base.repos.get_matching("fedora-source")
    r.enable()
    r = base.repos.get_matching("updates-source")
    r.enable()

    base.fill_sack(load_system_repo=False, load_available_repos=True)
    return base


def get_query_objects():
    """
    Get query objects for binary packages and source packages

    Returns: tuple of (binary_query, sources_query)
    """
    binaries = setup_base_repo()
    sources = setup_source_repo()
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


def process_requirements(reqs, dependencies, query, hints, pick_first,
                         follow_recommends):
    """
    Share code for recursing into requires or recommends
    """
    for require in reqs:
        required_packages = query.filter(provides=str(require), latest=True)

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
                                             dependencies, query, hints,
                                             pick_first, follow_recommends)
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
                    recurse_package_deps(required_packages[0], dependencies,
                                         query, hints, pick_first,
                                         follow_recommends)
                    continue
                # Packages not solved by 'hints' list
                # should be printed in red and we will cease
                # recursing here.
                for multichoice in required_packages:
                    dependencies["_MULTI_:" + multichoice.name] = multichoice

            continue

        # Exactly one package matched, so proceed down into it.
        recurse_package_deps(required_packages[0], dependencies, query,
                             hints, pick_first, follow_recommends)


def recurse_package_deps(pkg, dependencies, query, hints,
                         pick_first, follow_recommends):
    """
    Recursively search through dependencies and add them to the list
    """
    if pkg.name in dependencies:
        # Don't recurse the same dependency twice
        return
    dependencies[pkg.name] = pkg

    # Process Requires:
    process_requirements(pkg.requires, dependencies, query, hints, pick_first,
                         follow_recommends)
    if follow_recommends:
        process_requirements(pkg.recommends, dependencies, query, hints,
                             pick_first, follow_recommends)

def recurse_srpm_deps(source_pkg, dependencies, sources, query, hints,
                      pick_first, follow_recommends):
    """
    Recursively search through dependencies and add them to the list
    """
    # Process Requires:
    # There is no BuildRecommends concept, so we don't
    # need to worry about that.
    process_requirements(source_pkg.requires, dependencies, query, hints,
                         pick_first,
                         follow_recommends)


def recurse_build_deps(source_pkg, binaries, sources,
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
    recurse_srpm_deps(source_pkg, binaries, sources, binary_query,
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
                           binary_query, source_query,
                           hints, pick_first,
                           follow_recommends)

def print_package_name(pkgname, dependencies, full):
    """
    Parse the package name for the error state and
    print it with the correct verbosity.
    """

    printpkg = dependencies[pkgname]

    end_color = False
    if pkgname.startswith("_MULTI_:"):
        end_color = True
        pkgname = pkgname[8:]
        sys.stdout.write(Fore.RED)

    if full:
        print("%d:%s-%s-%s.%s" % (printpkg.epoch,
                                  printpkg.name,
                                  printpkg.version,
                                  printpkg.release,
                                  printpkg.arch))
    else:
        print(printpkg.name)

    if end_color:
        sys.stdout.write(Style.RESET_ALL)


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
def neededby(pkgnames, hint, recommends, merge, full_name, pick_first):
    """
    Look up the dependencies for each specified package and
    display them in a human-parseable format.
    """

    (binary_query, _) = get_query_objects()

    dependencies = {}
    for pkgname in pkgnames:
        pkg = get_pkg_by_name(binary_query, pkgname)

        if not merge:
            # empty the dependencies list and start over
            dependencies = {}

        recurse_package_deps(pkg, dependencies, binary_query,
                             hint, pick_first, recommends)

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

    if merge:
        # Print the complete set of dependencies together
        for key in sorted(dependencies, key=dependencies.get):
            print_package_name(key, dependencies, full_name)


@main.command(short_help="Get Source RPM")
@click.argument('pkgnames', nargs=-1)
@click.option('--full-name/--no-full-name', default=False)
def getsourcerpm(pkgnames, full_name):
    """
    Look up the SRPMs from which these binary RPMs were generated.

    This list will be displayed deduplicated and sorted.
    """
    (binary_query, source_query) = get_query_objects()

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
def neededtoselfhost(pkgnames, hint, recommends, merge, full_name,
                     pick_first, sources):
    """
    Look up the build dependencies for each specified package
    and all of their dependencies, recursively and display them
    in a human-parseable format.
    """

    (binary_query, source_query) = get_query_objects()

    binary_pkgs = {}
    source_pkgs = {}
    for pkgname in pkgnames:
        pkg = get_pkg_by_name(binary_query, pkgname)

        if not merge:
            binary_pkgs = {}
            source_pkgs = {}

        # Get the source RPM for this package
        spkg = get_srpm_for_package(source_query, pkg)
        recurse_build_deps(spkg, binary_pkgs, source_pkgs,
                           binary_query, source_query,
                           hint, pick_first, recommends)
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

    if merge:
        if sources:
            for key in sorted(source_pkgs, key=source_pkgs.get):
                print_package_name(key, source_pkgs, full_name)
        else:
            for key in sorted(binary_pkgs, key=binary_pkgs.get):
                print_package_name(key, binary_pkgs, full_name)