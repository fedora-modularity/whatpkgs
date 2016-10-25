#!/usr/bin/python3

"""
Tool for interacting with python3-dnf to get complicated dependency
information from yum/dnf repodata.
"""

import os
import queue
import threading
import whatpkgs
import click
import time

NUM_PROCS=os.sysconf("SC_NPROCESSORS_ONLN")


def print_package_name(filehandle, pkgname, dependencies, full):
    """
    Parse the package name for the error state and
    print it with the correct verbosity.
    """

    printpkg = dependencies[pkgname]

    if full:
        filehandle.write("%d:%s-%s-%s.%s\n" % (printpkg.epoch,
                                               printpkg.name,
                                               printpkg.version,
                                               printpkg.release,
                                               printpkg.arch))
    else:
        filehandle.write("%s\n" % printpkg.name)


@click.group()
def main():
    pass

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
@click.option('--rhel/--no-rhel', default=False,
              help="If --system is not specified, the use of --rhel will "
                   "give back results from the RHEL sample data. Otherwise, "
                   "Fedora sample data will be used.")
@click.option('--path', default="./%s" % time.asctime())
def neededtoselfhost(pkgnames, hint, recommends, full_name,
                     pick_first, sources, system, rhel, path):

    def selfhost_worker():
        while True:
            item = q.get()
            if item is None:
                break

            binary_pkgs = {}
            source_pkgs = {}
            ambiguities = []

            pkg = whatpkgs.get_pkg_by_name(query, item["pkg_name"])

            whatpkgs.recurse_self_host(pkg, binary_pkgs, source_pkgs,
                                       ambiguities, query, hint,
                                       pick_first, recommends)

            f = open(item["output_file"], 'w')

            if sources:
                for key in sorted(source_pkgs, key=source_pkgs.get):
                    # Skip the initial package
                    if key == item["pkg_name"]:
                        continue
                    print_package_name(f, key, source_pkgs, full_name)
            else:
                for key in sorted(binary_pkgs, key=binary_pkgs.get):
                    print_package_name(f, key, binary_pkgs, full_name)

            q.task_done()

    os.mkdir(path)

    query = whatpkgs.get_query_object(system, rhel)

    q = queue.Queue()
    threads = []
    for i in range(NUM_PROCS):
        t = threading.Thread(target=selfhost_worker)
        t.start()
        threads.append(t)

    for pkgname in pkgnames:
        output_file = os.path.join(path, pkgname)
        temp = {"pkg_name": pkgname,
                "output_file": output_file}
        q.put(temp)

    q.join()

    # stop workers
    for i in range(NUM_PROCS):
        q.put(None)
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
