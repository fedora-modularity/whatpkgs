#!/usr/bin/bash


# Packages that explicitly belong in the Base Runtime
# These are packages that are expected to maintain their public API for a very
# long time and are required for booting the system "(lights-on)"
EXPLICIT_BR="
    dracut
    gcc
    gcc-c++
    glibc
    glibc-common
    glibc-headers
    grub2
    grub2-efi
    kernel-core
    kernel-headers
    libcrypt
    libgcc
    libstdc++
    libstdc++-devel
"

FILTER_BR=""
for i in $EXPLICIT_BR; do
    FILTER_BR="$FILTER_BR --filter=$i"
done


# Packages that explicitly belong in the System Runtime
# Items listed here may also be dependencies for the Base Runtime, but we are
# electing to carry them with a different stability guarantee than BR.
# Items in the system runtime are required for POSIX compliance.
EXPLICIT_SR="
    binutils
    coreutils
    findutils
    shadow-utils
    systemd
"

FILTER_SR=""
for i in $EXPLICIT_SR; do
    FILTER_SR="$FILTER_SR --filter=$i"
done

# Packages that belong in the shared components
# These are packages that only show up in the dependencies of one of BR or SR,
# but for which we do not want to maintain any API guarantees, so we'll move
# them to the shared components list.
EXPLICIT_SHARED="
    fedora-logos \
    freetype
"



echo
echo "Generate the SRPM list for base runtime (\"lights-on\")"
./whatpkgs.py neededby --merge --no-recommends \
                      --hint=glibc-minimal-langpack \
                      --hint=fedora-release \
                      --hint=libcrypt \
                      --hint=cronie-noanacron \
                      --hint=coreutils \
                      ${FILTER_SR} \
                      ${EXPLICIT_BR} \
                      ${EXPLICIT_SHARED} \
| xargs \
./whatpkgs.py getsourcerpm --full-name \
| sort | tee sampledata/fedora/25/base-runtime-module-source-packages-prelim.txt


echo
echo "Generate the SRPM list for system runtime (POSIX)"
cat sampledata/fedora/25/toplevel-binary-packages.txt|xargs \
./whatpkgs.py neededby --merge --no-recommends \
                       --hint=glibc-minimal-langpack \
                       --hint=fedora-release \
                       --hint=libcrypt \
                       --hint=cronie-noanacron \
                       --hint=coreutils \
                       ${FILTER_BR} \
                       ${EXPLICIT_SR} \
                       ${EXPLICIT_SHARED} \
| xargs \
./whatpkgs.py getsourcerpm --full-name \
| sort | tee sampledata/fedora/25/system-runtime-module-source-packages-prelim.txt


echo
echo "Items that appear only in the base runtime belong to that module"
comm -2 -3 \
     sampledata/fedora/25/base-runtime-module-source-packages-prelim.txt \
     sampledata/fedora/25/system-runtime-module-source-packages-prelim.txt \
| sort | tee sampledata/fedora/25/base-runtime-module-definition-full.txt

echo
echo "Items that appear only in the system runtime belong to that module"
comm -1 -3 \
     sampledata/fedora/25/base-runtime-module-source-packages-prelim.txt \
     sampledata/fedora/25/system-runtime-module-source-packages-prelim.txt \
| sort | tee sampledata/fedora/25/system-runtime-module-definition-full.txt


echo
echo "Items common to both belong in the shared components module"
comm -1 -2 \
     sampledata/fedora/25/base-runtime-module-source-packages-prelim.txt \
     sampledata/fedora/25/system-runtime-module-source-packages-prelim.txt \
| sort | tee sampledata/fedora/25/shared-components-module-definition-full.txt


echo  "All remaining packages in the self-hosting list belong in gen-core-build"
cat sampledata/fedora/25/selfhosting-source-packages-full.txt \
| sort| tee sampledata/fedora/25/gen-core-build-module-definition-prelim.txt

cat sampledata/fedora/25/base-runtime-module-definition-full.txt \
    sampledata/fedora/25/system-runtime-module-definition-full.txt \
    sampledata/fedora/25/shared-components-module-definition-full.txt \
| sort | comm -2 -3 sampledata/fedora/25/gen-core-build-module-definition-prelim.txt - \
| sort | tee sampledata/fedora/25/gen-core-build-module-definition-full.txt


echo "Removing intermediate files"
rm -f sampledata/fedora/25/base-runtime-module-source-packages-prelim.txt \
      sampledata/fedora/25/system-runtime-module-source-packages-prelim.txt \
      sampledata/fedora/25/gen-core-build-module-definition-prelim.txt

