import dnf
import click
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


def setup_repo():
    """
    Enable only the official Fedora repositories

    Returns: dnf.Base containing all the package metadata from the standard
             repositories
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


def get_pkg_by_name(q, pkgname):
    """
    Try to find the package name as x86_64 and then noarch.
    This function will return exactly one result. If it finds zero or multiple
    packages that match the name, it will throw an error.
    """
    matched = q.filter(name=pkgname, arch='x86_64')
    if len(matched) > 1:
        raise TooManyPackagesException(pkgname)

    if len(matched) == 1:
        # Exactly one package matched
        # Technically it's possible for there to also be a noarch package
        # with the same name, which is an edge case I'm not optimizing for
        # yet.
        return matched[0]

    matched = q.filter(name=pkgname, arch='noarch')
    if len(matched) > 1:
        raise TooManyPackagesException(pkgname)

    if len(matched) == 1:
        # Exactly one package matched
        return matched[0]

    raise NoSuchPackageException(pkgname)


def recurse_package_deps(pkg, dependencies, query, choose, follow_recommends):
    """
    Recursively search through dependencies and add them to the list
    """
    if pkg.name in dependencies:
        # Don't recurse the same dependency twice
        return
    dependencies[pkg.name] = pkg

    for require in pkg.requires:
        required_packages = query.filter(provides=require)

        # TODO: handle 'choose' list
        # For now, we'll just pick the first entry

        recurse_package_deps(required_packages[0], dependencies, query,
                             choose, follow_recommends)

    if follow_recommends:
        for recommend in pkg.recommends:
            recommended_packages = query.filter(provides=recommend)

            # TODO: handle 'choose' list
            # For now, we'll just pick the first entry

            recurse_package_deps(recommended_packages[0], dependencies, query,
                                 choose, follow_recommends)


@click.group()
def main():
    pass


@main.command(short_help="Get package dependencies")
@click.argument('pkgnames', nargs=-1)
@click.option('--choose',
              help="""
Specify a package to be selected when more than one package could satisfy a
dependency. This option may be specified multiple times.

For example, it is recommended to use --choose=glibc-minimal-langpack
""")
@click.option('--recommends/--no-recommends', default=True)
def neededby(pkgnames, choose, recommends):
    """
    Look up the dependencies for each specified package and
    display them in a human-parseable format.
    """

    base = setup_repo()
    q = base.sack.query()

    for pkgname in pkgnames:
        pkg = get_pkg_by_name(q, pkgname)

        print(Fore.GREEN + Back.BLACK + "=== %s.%s ===" % (
            pkg.name, pkg.arch))
        print(Style.RESET_ALL, end='')

        dependencies = {}
        recurse_package_deps(pkg, dependencies, q, choose, recommends)

        for key in sorted(dependencies, key=dependencies.get):
            # Skip the initial package
            if key == pkgname:
                continue
            print(key)
