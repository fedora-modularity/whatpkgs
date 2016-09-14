# Sample data for Fedora 25

## toplevel-binary-packages.txt

The contents of this file were determined by manually going through the list of
POSIX utilities at
http://pubs.opengroup.org/onlinepubs/9699919799/idx/utilities.html and
determining the Fedora package to which they each belonged. There is no single
tool for this today; a mixture of `dnf repoquery` and guesswork was involved.


## toplevel-source-packages.txt

This file contains the full ENVR for the Source RPMs that provide the contents
of the toplevel-binary-packages.txt. It was created by running the command:
```
cat sampledata/toplevel-binary-packages.txt| xargs \
whatpkgs getsourcerpm --full-name
```

## runtime-binary-dependency-packages-short.txt

This file contains all of the binary packages necessary to support the contents
of toplevel-binary-packages.txt. It was created by running the command:
```
cat sampledata/toplevel-binary-packages.txt|xargs \
whatpkgs neededby --merge --no-recommends \
                  --hint=glibc-minimal-langpack \
                  --hint=fedora-release \
                  --hint=libcrypt-nss \
                  --hint=cronie-noanacron \
                  --hint=coreutils
```

## runtime-binary-dependency-packages-full.txt

This file contains all of the binary packages necessary to support the contents
of toplevel-binary-packages.txt and containing the full ENVR of those packages.
It was created by running the command:
```
cat sampledata/toplevel-binary-packages.txt|xargs \
whatpkgs neededby --merge --no-recommends --full-name \
                  --hint=glibc-minimal-langpack \
                  --hint=fedora-release \
                  --hint=libcrypt-nss \
                  --hint=cronie-noanacron \
                  --hint=coreutils
```

## runtime-source-packages-short.txt

This file contains the list of Source RPMs that provide the contents of the
toplevel-binary-packages.txt. It was created by running the command:
```
cat sampledata/runtime-binary-dependency-packages-short.txt| xargs \
whatpkgs getsourcerpm
```

## runtime-source-packages-full.txt

This file contains the full ENVR for the Source RPMs that provide the contents
of the toplevel-binary-packages.txt. It was created by running the command:
```
cat sampledata/runtime-binary-dependency-packages-short.txt| xargs \
whatpkgs getsourcerpm --full-name
```

## selfhosting-binary-packages-short.txt
This file contains every package needed to self-host the packages from
runtime-binary-dependency-packages-short.txt. It was created by running:
```
cat sampledata/runtime-binary-dependency-packages-short.txt | xargs \
whatpkgs neededtoselfhost --merge --no-recommends \
                          --pick-first --no-sources \
                          --hint=glibc-minimal-langpack \
                          --hint=fedora-release \
                          --hint=libcrypt-nss \
                          --hint=cronie-noanacron \
                          --hint=coreutils

```

## selfhosting-binary-packages-full.txt
This file contains every package needed to self-host the packages from
runtime-binary-dependency-packages-short.txt. It was created by running:
```
cat sampledata/runtime-binary-dependency-packages-short.txt | xargs \
whatpkgs neededtoselfhost --merge --no-recommends --full-name \
                          --pick-first --no-sources \
                          --hint=glibc-minimal-langpack \
                          --hint=fedora-release \
                          --hint=libcrypt-nss \
                          --hint=cronie-noanacron \
                          --hint=coreutils
```

## selfhosting-source-packages-short.txt
This file contains the list of source packages forevery package needed to
self-host the packages from runtime-binary-dependency-packages-short.txt.
It was created by running:
```
cat sampledata/runtime-binary-dependency-packages-short.txt | xargs \
whatpkgs neededtoselfhost --merge --no-recommends \
                          --pick-first --sources \
                          --hint=glibc-minimal-langpack \
                          --hint=fedora-release \
                          --hint=libcrypt-nss \
                          --hint=cronie-noanacron \
                          --hint=coreutils
```

## selfhosting-source-packages-full.txt
This file contains the list of source packages forevery package needed to
self-host the packages from runtime-binary-dependency-packages-short.txt.
It was created by running:
```
cat sampledata/runtime-binary-dependency-packages-short.txt | xargs \
whatpkgs neededtoselfhost --merge --no-recommends --full-name \
                          --pick-first --sources \
                          --hint=glibc-minimal-langpack \
                          --hint=fedora-release \
                          --hint=libcrypt-nss \
                          --hint=cronie-noanacron \
                          --hint=coreutils
```

