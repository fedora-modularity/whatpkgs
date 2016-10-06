# whatpkgs

The whatpkgs python module is an interface to the DNF API to perform
complicated lookups on package dependencies.

This tool must be executed from the root of the git checkout in order for it
to properly locate the frozen repository data.

## Setup
This tool has been tested on Fedora 24 and 25. It requires the following
pre-requisites (which includes DNF 2.0):
```
dnf install fedora-repos-rawhide
dnf update dnf --enablerepo=rawhide
dnf install python3-click python3-colorama
```

## How to run:

### Get the source RPM for one or more packages
```
Usage: whatpkgs.py getsourcerpm [OPTIONS] [PKGNAMES]...

  Look up the SRPMs from which these binary RPMs were generated.

  This list will be displayed deduplicated and sorted.

Options:
  --full-name / --no-full-name
  --system / --no-system        If --system is specified, use the 'fedora',
                                'updates', 'source' and 'updates-source'
                                repositories from the local system
                                configuration. Otherwise, use the static data
                                from the sampledata directory.
  --help                        Show this message and exit.
```


### Get the recursive list of all runtime dependencis for one or more packages
```
Usage: whatpkgs.py neededby [OPTIONS] [PKGNAMES]...

  Look up the dependencies for each specified package and display them in a
  human-parseable format.

Options:
  --hint TEXT                     Specify a package to be selected when more
                                  than one package could satisfy a
                                  dependency.
                                  This option may be specified multiple times.
                                  For example, it is recommended to use
                                  --hint=glibc-minimal-langpack
  --recommends / --no-recommends
  --merge / --no-merge
  --full-name / --no-full-name
  --pick-first / --no-pick-first  If multiple packages could satisfy a
                                  dependency and no --hint package will
                                  fulfill the requirement, automatically
                                  select one from the list.

                                  Note: this result
                                  may differ between runs depending upon how
                                  the list is
                                  sorted. It is recommended to use
                                  --hint instead, where practical.
  --system / --no-system          If --system is specified, use the 'fedora',
                                  'updates', 'source' and 'updates-source'
                                  repositories from the local system
                                  configuration. Otherwise, use the static
                                  data from the sampledata directory.
  --help                          Show this message and exit.
```

### Get the list of packages required to self-host for one or more packages
"Self-hosting" in this context means "all of the packages necessary to be able
to build all the packages listed on the command line, plus recursively any
packages required to build those BuildRequires as well.

```
Usage: whatpkgs.py neededtoselfhost [OPTIONS] [PKGNAMES]...

  Look up the build dependencies for each specified package and all of their
  dependencies, recursively and display them in a human-parseable format.

Options:
  --hint TEXT                     Specify a package to be selected when more
                                  than one package could satisfy a
                                  dependency.
                                  This option may be specified multiple times.
                                  For example, it is recommended to use
                                  --hint=glibc-minimal-langpack

                                  For build
                                  dependencies, the default is to exclude
                                  Recommends: from the
                                  dependencies of the
                                  BuildRequires.
  --recommends / --no-recommends
  --merge / --no-merge
  --full-name / --no-full-name
  --sources / --no-sources
  --pick-first / --no-pick-first  If multiple packages could satisfy a
                                  dependency and no --hint package will
                                  fulfill the requirement, automatically
                                  select one from the list.

                                  Note: this result
                                  may differ between runs depending upon how
                                  the list is
                                  sorted. It is recommended to use
                                  --hint instead, where practical.
  --system / --no-system          If --system is specified, use the 'fedora',
                                  'updates', 'source' and 'updates-source'
                                  repositories from the local system
                                  configuration. Otherwise, use the static
                                  data from the sampledata directory.
  --help                          Show this message and exit.
```