#!/usr/bin/bash

echo
echo "Generate the SRPM list for base runtime ("lights-on")"
./whatpkgs.py neededby --merge --no-recommends \
                      --hint=glibc-minimal-langpack \
                      --hint=fedora-release \
                      --hint=libcrypt-nss \
                      --hint=cronie-noanacron \
                      --hint=coreutils \
                      grub2 grub2-efi kernel-core kernel-headers \
| xargs \
./whatpkgs.py getsourcerpm --full-name \
| sort | tee sampledata/fedora/25beta/base-runtime-module-source-packages-prelim.txt


echo
echo "Generate the SRPM list for system runtime (POSIX)"
cat sampledata/toplevel-binary-packages.txt|xargs \
./whatpkgs.py neededby --merge --no-recommends \
                       --hint=glibc-minimal-langpack \
                       --hint=fedora-release \
                       --hint=libcrypt-nss \
                       --hint=cronie-noanacron \
                       --hint=coreutils \
                       --filter grub2 \
                       --filter grub2-efi \
                       --filter kernel-core \
                       --filter kernel-headers \
| xargs \
./whatpkgs.py getsourcerpm --full-name \
| sort | tee sampledata/fedora/25beta/system-runtime-module-source-packages-prelim.txt


echo
echo "Items that appear only in the base runtime belong to that module"
comm -2 -3 \
     sampledata/fedora/25beta/base-runtime-module-source-packages-prelim.txt \
     sampledata/fedora/25beta/system-runtime-module-source-packages-prelim.txt \
| sort | tee sampledata/fedora/25beta/base-runtime-module-definition-full.txt

echo
echo "Items that appear only in the system runtime belong to that module"
comm -1 -3 \
     sampledata/fedora/25beta/base-runtime-module-source-packages-prelim.txt \
     sampledata/fedora/25beta/system-runtime-module-source-packages-prelim.txt \
| sort | tee sampledata/fedora/25beta/system-runtime-module-definition-full.txt


echo
echo "Items common to both belong in the shared components module"
comm -1 -2 \
     sampledata/fedora/25beta/base-runtime-module-source-packages-prelim.txt \
     sampledata/fedora/25beta/system-runtime-module-source-packages-prelim.txt \
| sort | tee sampledata/fedora/25beta/shared-components-module-definition-full.txt


echo "Removing intermediate files"
rm -f sampledata/fedora/25beta/base-runtime-module-source-packages-prelim.txt \
      sampledata/fedora/25beta/system-runtime-module-source-packages-prelim.txt

