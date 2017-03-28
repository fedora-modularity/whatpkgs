#!/usr/bin/python3

"""
Tool for interacting with python3-dnf to get complicated dependency
information from yum/dnf repodata.
"""

import os
import platform
import sys
import pprint
import dnf
import click
from collections import namedtuple
from queue import Queue
from threading import Thread
from colorama import Fore, Back, Style

NUM_PROCS = os.sysconf("SC_NPROCESSORS_ONLN")

multi_arch = None
primary_arch = platform.machine()
if primary_arch == "x86_64":
    multi_arch = "i686"

PackageContext = namedtuple("DepContext", ["dependencies",
                                           "ambiguities",
                                           "query",
                                           "hints",
                                           "filters",
                                           "whatreqs",
                                           "do_pick_first",
                                           "do_recommends"])

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


def _setup_static_repo(base, reponame, path):
    repo = dnf.repo.Repo(reponame, base.conf)

    repo.mirrorlist = None
    repo.metalink = None
    repo.baseurl = "file://" + path
    repo.name = reponame
    try:
        repo._id = reponame
    except AttributeError:
        print("DNF 2.x required.", file=sys.stderr)
        sys.exit(1)
    base.repos.add(repo)
    repo.load()
    repo.enable()
    repo._md_expire_cache()


def setup_repo(use_system, use_rhel, version="25"):
    """
    Enable only the official Fedora repositories

    Returns: dnf.Base containing all the package metadata from the standard
             repositories for binary RPMs
    """
    base = dnf.Base()

    if use_system:
        base.read_all_repos()
        repo = base.repos.all()
        repo.disable()
        repo = base.repos.get_matching("fedora")
        repo.enable()
        repo = base.repos.get_matching("updates")
        repo.enable()
        repo = base.repos.get_matching("fedora-source")
        repo.enable()
        repo = base.repos.get_matching("updates-source")
        repo.enable()

    elif use_rhel:
        # Load the static data for RHEL
        dir_path = os.path.dirname(os.path.realpath(__file__))
        repo_path = os.path.join(dir_path,
            "sampledata/repodata/RHEL-7/7.3-Beta/Server/%s/os/" % primary_arch)
        _setup_static_repo(base, "static-rhel7.3beta-binary", repo_path)

        repo_path = os.path.join(dir_path,
            "sampledata/repodata/RHEL-7/7.3-Beta/Server-optional/%s/os/" %
                                 primary_arch)
        _setup_static_repo(base,
                           "static-rhel7.3beta-optional-binary",
                           repo_path)

        repo_path = os.path.join(dir_path,
            "sampledata/repodata/RHEL-7/7.3-Beta/Server/source/tree/")
        _setup_static_repo(base, "static-rhel7.3beta-source", repo_path)

        repo_path = os.path.join(dir_path,
            "sampledata/repodata/RHEL-7/7.3-Beta/Server-optional/source/tree/")
        _setup_static_repo(base,
                           "static-rhel7.3beta-optional-source",
                           repo_path)

    else:
        # Load the static data for Fedora
        dir_path = os.path.dirname(os.path.realpath(__file__))
        repo_path = os.path.join(dir_path,
           "sampledata/repodata/fedora/linux/development/%s/Everything/%s/"
           "/os" % (version, primary_arch))
        _setup_static_repo(base, "static-f%s-beta-binary" % version, repo_path)

        repo_path = os.path.join(dir_path,
           "sampledata/repodata/fedora/linux/development/%s/Everything/source"
           "/tree/" % version)
        _setup_static_repo(base, "static-f%s-beta-source" % version, repo_path)

        # Add override repositories for modularity
        repo_path = os.path.join(dir_path,
           "sampledata/repodata/fedora/linux/development/%s/gencore-override"
           "/%s/os" % (version, primary_arch))
        _setup_static_repo(base,
                           "static-gencore-override-f%s-binary" % version,
                           repo_path)

        repo_path = os.path.join(dir_path,
           "sampledata/repodata/fedora/linux/development/%s/gencore-override"
           "/source/tree/" % version)
        _setup_static_repo(base, "static-gencore-override-source", repo_path)

    base.fill_sack(load_system_repo=False, load_available_repos=True)
    return base


def get_query_object(use_system, use_rhel, version):
    """
    Get query objects for binary packages and source packages

    Returns: query object for source and binaries
    """
    base = setup_repo(use_system, use_rhel, version)

    return base.sack.query()


def get_pkg_by_name(q, pkgname, arch=None):
    """
    Try to find the package name as primary_arch, multi_arch and then noarch.
    This function will return exactly one result. If it finds zero or multiple
    packages that match the name, it will throw an error.
    """

    # If we were requested to search for a specific architecture
    if arch:
        matched = q.filter(name=pkgname, latest=True, arch=arch)
        if len(matched) > 1:
            raise TooManyPackagesException(pkgname)
        if len(matched) == 1:
            # Exactly one package matched.
            return matched[0]
        raise NoSuchPackageException(pkgname)

    # Otherwise, check the primary arch, multi-arch and noarch packages
    matched = q.filter(name=pkgname, latest=True, arch=primary_arch)
    if len(matched) > 1:
        raise TooManyPackagesException(pkgname)

    if len(matched) == 1:
        # Exactly one package matched. We'll prioritize the archful package if
        # the same package would satisfy a multi-arch version as well.
        # Technically it's possible for there to also be a noarch package
        # with the same name, which is an edge case I'm not optimizing for
        # yet.
        return matched[0]

    if multi_arch:
        matched = q.filter(name=pkgname, latest=True, arch=multi_arch)
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


def get_srpm_for_package(query, pkg):
    # Get just the base name of the SRPM
    try:
        (sourcename, _, _, _, _) = splitFilename(pkg.sourcerpm)
    except Exception:
        print("Failure: %s(%s)" % (pkg.sourcerpm, pkg.name))
        raise

    matched = query.filter(name=sourcename, latest=True, arch='src')
    if len(matched) > 1:
        raise TooManyPackagesException(pkg.name)

    if len(matched) == 1:
        # Exactly one package matched
        return matched[0]

    raise NoSuchPackageException(pkg.name)


def get_srpm_for_package_name(query, pkgname):
    """
    For a given package, retrieve a reference to its source RPM
    """
    pkg = get_pkg_by_name(query, pkgname)

    return get_srpm_for_package(query, pkg)

def append_requirement(reqs, parent, pkg, filters, whatreqs):
    """
    Check if this package is in the filter list. If it is, then
    do not add it to the list of packages to recurse into.
    """
    if whatreqs is not None and pkg.name in whatreqs:
        print("%s is pulled in by %s" % (pkg.name, parent.name),
              file=sys.stderr)

    if filters is None or pkg.name not in filters:
        reqs.append(pkg)

def get_requirements(parent, reqs, pkg_ctx):
    """
    Share code for recursing into requires or recommends
    """
    requirements = []

    for require in reqs:
        required_packages = pkg_ctx.query.filter(provides=require,
                                                 latest=True,
                                                 arch=primary_arch)

        # Check for multi-arch packages satisfying it
        if len(required_packages) == 0 and multi_arch:
            required_packages = pkg_ctx.query.filter(provides=require,
                                                     latest=True,
                                                     arch=multi_arch)

        # Check for noarch packages satisfying it
        if len(required_packages) == 0:
            required_packages = pkg_ctx.query.filter(provides=require,
                                                     latest=True,
                                                     arch='noarch')

        # If there are no dependencies, just return
        if len(required_packages) == 0:
            print("No package for [%s] required by [%s-%s-%s.%s]" % (
                    str(require),
                    parent.name, parent.version,
                    parent.release, parent.arch),
                  file=sys.stderr)
            continue

        # Check for multiple possible packages
        if len(required_packages) > 1:
            # Handle 'hints' list
            found = False
            for choice in pkg_ctx.hints:
                for rpkg in required_packages:
                    if rpkg.name == choice:
                        # This has been disambiguated; use this one
                        found = True
                        append_requirement(requirements,
                                           parent,
                                           rpkg,
                                           pkg_ctx.filters,
                                           pkg_ctx.whatreqs)
                        break
                if found:
                    # Don't keep looking once we find a match
                    break

            if not found:
                if pkg_ctx.do_pick_first:
                    # First try to use something we've already discovered
                    for rpkg in required_packages:
                        if rpkg.name in pkg_ctx.dependencies:
                            return

                    # The user instructed processing to just take the first
                    # entry in the list.
                    for rpkg in required_packages:
                        if rpkg.arch == 'noarch' or rpkg.arch == \
                                primary_arch or rpkg.arch == multi_arch:
                            append_requirement(requirements,
                                               parent,
                                               rpkg,
                                               pkg_ctx.filters,
                                               pkg_ctx.whatreqs)
                            break
                    continue
                # Packages not solved by 'hints' list
                # should be added to the ambiguities list
                unresolved = {}
                for rpkg in required_packages:
                    unresolved["%s#%s" % (rpkg.name, rpkg.arch)] = rpkg
                pkg_ctx.ambiguities.append(unresolved)

            continue

        # Exactly one package matched, so proceed down into it.
        append_requirement(requirements, parent, required_packages[0],
                           pkg_ctx.filters, pkg_ctx.whatreqs)

    return requirements


def recurse_package_deps(pkg, dependencies, ambiguities,
                         query, hints, filters, whatreqs,
                         pick_first, follow_recommends):
    """
    Recursively search through dependencies and add them to the list
    """
    depname = "%s#%s" % (pkg.name, pkg.arch)
    if depname in dependencies:
        # Don't recurse the same dependency twice
        return
    dependencies[depname] = pkg

    # Process Requires:
    deps = get_requirements(pkg, pkg.requires, dependencies,
                            ambiguities, query, hints,
                            filters, whatreqs,
                            pick_first)

    try:
        # Process Requires(pre|post)
        prereqs = get_requirements(pkg, pkg.requires_pre, dependencies,
                                   ambiguities, query, hints,
                                   filters, whatreqs,
                                   pick_first)
        deps.extend(prereqs)
    except AttributeError:
        print("DNF 2.x required.", file=sys.stderr)
        sys.exit(1)

    if follow_recommends:
        recommends = get_requirements(pkg, pkg.recommends, dependencies,
                                      ambiguities, query, hints,
                                      filters, whatreqs,
                                      pick_first)
        deps.extend(recommends)

    for dep in deps:
        recurse_package_deps(dep, dependencies, ambiguities, query,
                             hints, filters, whatreqs,
                             pick_first, follow_recommends)


def recurse_self_host(binary_pkg, binaries, sources,
                      ambiguities, query, hints,
                      filters, whatreqs,
                      pick_first, follow_recommends):
    """
    Recursively determine all build dependencies for this package
    """

    depname = "%s#%s" % (binary_pkg.name, binary_pkg.arch)
    if depname in binaries:
        # Don't process the same binary RPM twice
        return

    binaries[depname] = binary_pkg

    # Process strict Requires:
    deps = get_requirements(binary_pkg, binary_pkg.requires, binaries,
                            ambiguities, query, hints,
                            filters, whatreqs, pick_first)

    # Process Requires(pre|post):
    prereqs = get_requirements(binary_pkg, binary_pkg.requires_pre,
                               binaries, ambiguities, query, hints,
                               filters, whatreqs, pick_first)
    deps.extend(prereqs)

    if follow_recommends:
        # Process Recommends:
        recommends = get_requirements(binary_pkg, binary_pkg.recommends,
                                      binaries, ambiguities, query, hints,
                                      filters, whatreqs, pick_first)
        deps.extend(recommends)

    # Now get the build dependencies for this package
    source_pkg = get_srpm_for_package(query, binary_pkg)

    if source_pkg.name not in sources:
        # Don't process the same Source RPM twice
        sources[source_pkg.name] = source_pkg

        # Get the BuildRequires for this Source RPM
        buildreqs = get_requirements(source_pkg, source_pkg.requires,
                                     binaries, ambiguities, query, hints,
                                     filters, whatreqs, pick_first)
        deps.extend(buildreqs)

    for dep in deps:
        recurse_self_host(dep, binaries, sources, ambiguities, query, hints,
                          filters, whatreqs, pick_first, follow_recommends)


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
        if printpkg.arch == multi_arch:
            print("%s#%s" % (printpkg.name, printpkg.arch))
        else:
            print("%s" % printpkg.name)


def resolve_ambiguity(dependencies, ambiguity):
    """
    Determine if any of the contents of an ambiguous lookup
    is already resolved by something in the dependencies.
    """
    for key in sorted(ambiguity, key=ambiguity.get):
        if key in dependencies:
            return True
    return False


def _split_pkgname(name):
    splitname = name.rsplit("#", 2)
    pkgname = splitname[0]
    arch = None
    if len(splitname) > 1:
        arch = splitname[1]

    return (pkgname, arch)


def get_all_requirements(pkg_ctx, pkg_queue):
    while True:
        # Get all requested dependencies
        pkg = pkg_queue.get()
        if pkg is None:
            break;

        depname = "%s#%s" % (pkg.name, pkg.arch)
        if depname in pkg_ctx.dependencies:
            # Don't recurse the same dependency twice
            pkg_queue.task_done()
            continue
        pkg_ctx.dependencies[depname] = pkg

        #print("Processing [%s]" % depname, file=sys.stderr)

        # Process Requires:
        deps = get_requirements(pkg, pkg.requires, pkg_ctx)

        try:
            # Process Requires(pre|post)
            prereqs = get_requirements(pkg, pkg.requires_pre, pkg_ctx)
            deps.extend(prereqs)
        except AttributeError:
            print("DNF 2.x required.", file=sys.stderr)
            sys.exit(1)

        if pkg_ctx.do_recommends:
            recommends = get_requirements(pkg, pkg.recommends, pkg_ctx)
            deps.extend(recommends)

        for dep in deps:
            pkg_queue.put(dep);

        pkg_queue.task_done();

def get_parallel_deps(pkgs, dependencies, ambiguities, query, hint,
                      filter, whatreqs, pick_first, recommends):

    # Store all of the options here in a namedtuple to make it easier to
    # pass around.
    pkg_ctx = PackageContext(dependencies=dependencies,
                             ambiguities=ambiguities,
                             query=query,
                             hints=hint,
                             filters=filter,
                             whatreqs=whatreqs,
                             do_pick_first=pick_first,
                             do_recommends=recommends)

    # Create a Queue of packages to look up
    package_queue = Queue()

    # Spin up threads for processing the dependencies
    # TODO: add command-line argument to set this. For now, select threads
    # equal to the number of available processors.
    threads = []
    for i in range(NUM_PROCS):
        worker = Thread(target=get_all_requirements,
                        args=(pkg_ctx, package_queue,))
        worker.setDaemon(True)
        worker.start()
        threads.append(worker)

    # initialized the Queue with the top-level packages.
    for pkg in pkgs:
        package_queue.put(pkg);

    # Wait for all the magic to happen
    package_queue.join();

    # Terminate worker threads
    for i in range(NUM_PROCS):
        package_queue.put(None);
    for worker in threads:
        worker.join()

    # Check for unresolved deps in the list that are present in the
    # dependencies. This happens when one package has an ambiguous dep but
    # another package has an explicit dep on the same package.
    # This list comprehension just returns the set of dictionaries that
    # are not resolved by other entries
    ambiguities = [x for x in ambiguities
                   if not resolve_ambiguity(dependencies, x)]


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
@click.option('--filter', multiple=True,
              help="""
Specify a package to be skipped during processing. This option may be
specified multiple times.

This is useful when some packages are provided by a lower-level module
already contains the package and its dependencies.
""")
@click.option('--whatreqs', multiple=True,
              help="""
Specify a package that you want to identify what pulls it into the complete
set. This option may be specified multiple times.
""")
@click.option('--recommends/--no-recommends', default=True)
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
@click.option('--rhel/--no-rhel', default=False,
              help="If --system is not specified, the use of --rhel will "
                   "give back results from the RHEL sample data. Otherwise, "
                   "Fedora sample data will be used.")
@click.option('--version', default="25",
              help="Specify the version of the OS sampledata to compare "
                   "against.")
def neededby(pkgnames, hint, filter, whatreqs, recommends, full_name,
             pick_first, system, rhel, version):
    """
    Look up the dependencies for each specified package and
    display them in a human-parseable format.
    """

    query = get_query_object(system, rhel, version)

    dependencies = {}
    ambiguities = []
    pkgs = []
    for fullpkgname in pkgnames:
        (pkgname, arch) = _split_pkgname(fullpkgname)

        if pkgname in filter:
            # Skip this if we explicitly filtered it out
            continue

        pkgs.append(get_pkg_by_name(query, pkgname, arch))


    get_parallel_deps(pkgs, dependencies, ambiguities, query, hint,
                      filter, whatreqs, pick_first, recommends)


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
@click.option('--rhel/--no-rhel', default=False,
              help="If --system is not specified, the use of --rhel will "
                   "give back results from the RHEL sample data. Otherwise, "
                   "Fedora sample data will be used.")
@click.option('--version', default="25",
              help="Specify the version of the OS sampledata to compare "
                   "against.")
def getsourcerpm(pkgnames, full_name, system, rhel, version):
    """
    Look up the SRPMs from which these binary RPMs were generated.

    This list will be displayed deduplicated and sorted.
    """
    query = get_query_object(system, rhel, version)

    srpm_names = {}
    for fullpkgname in pkgnames:
        (pkgname, arch) = _split_pkgname(fullpkgname)

        pkg = get_srpm_for_package_name(query, pkgname)

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
@click.option('--filter', multiple=True,
              help="""
Specify a package to be skipped during processing. This option may be
specified multiple times.

This is useful when some packages are provided by a lower-level module
already contains the package and its dependencies.
""")
@click.option('--whatreqs', multiple=True,
              help="""
Specify a package that you want to identify what pulls it into the complete
set. This option may be specified multiple times.
""")
@click.option('--system/--no-system', default=False,
              help="If --system is specified, use the 'fedora', 'updates', "
                   "'source' and 'updates-source' repositories from the local "
                   "system configuration. Otherwise, use the static data from "
                   "the sampledata directory.")
@click.option('--rhel/--no-rhel', default=False,
              help="If --system is not specified, the use of --rhel will "
                   "give back results from the RHEL sample data. Otherwise, "
                   "Fedora sample data will be used.")
@click.option('--version', default="25",
              help="Specify the version of the OS sampledata to compare "
                   "against.")
def neededtoselfhost(pkgnames, hint, recommends, merge, full_name,
                     pick_first, filter, whatreqs,
                     sources, system, rhel, version):
    """
    Look up the build dependencies for each specified package
    and all of their dependencies, recursively and display them
    in a human-parseable format.
    """

    query = get_query_object(system, rhel, version)

    binary_pkgs = {}
    source_pkgs = {}
    ambiguities = []
    for fullpkgname in pkgnames:
        (pkgname, arch) = _split_pkgname(fullpkgname)

        if pkgname in filter:
            # Skip this if we explicitly filtered it out
            continue

        pkg = get_pkg_by_name(query, pkgname, arch)

        if not merge:
            binary_pkgs = {}
            source_pkgs = {}
            ambiguities = []

        recurse_self_host(pkg, binary_pkgs, source_pkgs,
                          ambiguities, query, hint, filter,
                          whatreqs, pick_first, recommends)

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

@main.command(short_help="Debug missing Provides")
@click.argument('requires', nargs=1)

@click.option('--system/--no-system', default=False,
              help="If --system is specified, use the 'fedora', 'updates', "
                   "'source' and 'updates-source' repositories from the local "
                   "system configuration. Otherwise, use the static data from "
                   "the sampledata directory.")
@click.option('--rhel/--no-rhel', default=False,
              help="If --system is not specified, the use of --rhel will "
                   "give back results from the RHEL sample data. Otherwise, "
                   "Fedora sample data will be used.")
@click.option('--version', default="25",
              help="Specify the version of the OS sampledata to compare "
                   "against.")
def debugprovides(requires, system, rhel, version):
    query = get_query_object(system, rhel, version)

    required_packages = query.filter(provides=requires, latest=True,
                                     arch=primary_arch)

    if len(required_packages) == 0 and multi_arch:
        required_packages = query.filter(provides=requires, latest=True,
                                            arch=multi_arch)

    if len(required_packages) == 0:
        required_packages = query.filter(provides=requires, latest=True,
                                            arch='noarch')


    # If there are no dependencies, just return
    if len(required_packages) == 0:
        print("No package for [%s]" % (str(requires)), file=sys.stderr)
        sys.exit(1)

    for pkg in required_packages:
        print(repr(pkg))



if __name__ == "__main__":
    main()
