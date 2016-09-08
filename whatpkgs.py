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


def get_srpm_for_package(bq, sq, pkgname):
    """
    For a given package, retrieve a reference to its source RPM
    """
    pkg = get_pkg_by_name(bq, pkgname)

    # Get just the base name of the SRPM
    (sourcename, _, _, _, _) = splitFilename(pkg.sourcerpm)

    matched = sq.filter(name=sourcename, latest=True, arch='src')
    if len(matched) > 1:
        raise TooManyPackagesException(pkgname)

    if len(matched) == 1:
        # Exactly one package matched
        return matched[0]

    raise NoSuchPackageException(pkgname)


def process_requirements(reqs, dependencies, query, hints,
                         follow_recommends):
    """
    Share code for recursing into requires or recommends
    """
    for require in reqs:
        required_packages = query.filter(provides=require, latest=True)

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
                                             follow_recommends)
                        break
                if found:
                    # Don't keep looking once we find a match
                    break

            if not found:
                # Packages not solved by 'hints' list
                # should be printed in red and we will cease
                # recursing here.
                for multichoice in required_packages:
                    dependencies[Fore.RED +
                                 multichoice.name +
                                 Style.RESET_ALL] = multichoice

            continue

        # Exactly one package matched, so proceed down into it.
        recurse_package_deps(required_packages[0], dependencies, query,
                             hints, follow_recommends)


def recurse_package_deps(pkg, dependencies, query, hints, follow_recommends):
    """
    Recursively search through dependencies and add them to the list
    """
    if pkg.name in dependencies:
        # Don't recurse the same dependency twice
        return
    dependencies[pkg.name] = pkg

    # Process Requires:
    process_requirements(pkg.requires, dependencies, query, hints,
                         follow_recommends)
    if follow_recommends:
        process_requirements(pkg.recommends, dependencies, query, hints,
                             follow_recommends)

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
def neededby(pkgnames, hint, recommends):
    """
    Look up the dependencies for each specified package and
    display them in a human-parseable format.
    """

    base = setup_base_repo()
    q = base.sack.query()

    for pkgname in pkgnames:
        pkg = get_pkg_by_name(q, pkgname)

        print(Fore.GREEN + Back.BLACK + "=== %s.%s ===" % (
            pkg.name, pkg.arch) + Style.RESET_ALL)

        dependencies = {}
        recurse_package_deps(pkg, dependencies, q, hint, recommends)

        for key in sorted(dependencies, key=dependencies.get):
            # Skip the initial package
            if key == pkgname:
                continue
            print(key)


@main.command(short_help="Get Source RPM")
@click.argument('pkgnames', nargs=-1)
def getsourcerpm(pkgnames):
    """
    Look up the SRPMs from which these binary RPMs were generated.

    This list will be displayed deduplicated and sorted.
    """
    base = setup_base_repo()
    bq = base.sack.query()

    sources = setup_source_repo()
    sq = sources.sack.query()

    sources = setup_source_repo()

    srpm_names = {}
    for pkgname in pkgnames:
        pkg = get_srpm_for_package(bq, sq, pkgname)

        srpm_names[pkg.name] = pkg

    for key in sorted(srpm_names, key=srpm_names.get):
        print(key)
