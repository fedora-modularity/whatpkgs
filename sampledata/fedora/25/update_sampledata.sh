#!/bin/bash

set -x #echo on

cat sampledata/fedora/25/toplevel-binary-packages.txt| xargs \
./whatpkgs.py getsourcerpm --full-name \
| tee sampledata/fedora/25/toplevel-source-packages.txt


cat sampledata/fedora/25/toplevel-binary-packages.txt|xargs \
./whatpkgs.py neededby --merge --no-recommends \
                       --hint=coreutils \
                       --hint=cronie-noanacron \
                       --hint=fedora-release \
                       --hint=glibc-minimal-langpack \
                       --hint=libcrypt-nss \
                       --hint=python-libs \
| tee sampledata/fedora/25/runtime-binary-dependency-packages-short.txt


cat sampledata/fedora/25/toplevel-binary-packages.txt|xargs \
./whatpkgs.py neededby --merge --no-recommends --full-name \
                       --hint=coreutils \
                       --hint=cronie-noanacron \
                       --hint=fedora-release \
                       --hint=glibc-minimal-langpack \
                       --hint=libcrypt-nss \
                       --hint=python-libs \
| tee sampledata/fedora/25/runtime-binary-dependency-packages-full.txt


cat sampledata/fedora/25/runtime-binary-dependency-packages-short.txt| xargs \
./whatpkgs.py getsourcerpm \
| tee sampledata/fedora/25/runtime-source-packages-short.txt


cat sampledata/fedora/25/runtime-binary-dependency-packages-short.txt| xargs \
./whatpkgs.py getsourcerpm --full-name \
| tee sampledata/fedora/25/runtime-source-packages-full.txt


cat sampledata/fedora/25/toplevel-binary-packages.txt | xargs \
./whatpkgs.py neededtoselfhost --merge --no-recommends --full-name \
                               --no-sources \
                               --hint=coreutils \
                               --hint=cronie-noanacron \
                               --hint=environment-modules \
                               --hint=fedora-logos-httpd \
                               --hint=fedora-release \
                               --hint=glibc-minimal-langpack \
                               --hint=gnuplot \
                               --hint=infinipath-psm \
                               --hint=java-1.8.0-openjdk-javadoc \
                               --hint=kernel-core \
                               --hint=kernel-devel \
                               --hint=libcrypt-nss \
                               --hint=libverto-libev \
                               --hint=perl-Archive-Extract-bz2-bunzip2 \
                               --hint=perl-Archive-Extract-gz-gzip \
                               --hint=perl-Archive-Extract-lzma-Compress-unLZMA \
                               --hint=perl-Archive-Extract-tar-tar \
                               --hint=perl-Archive-Extract-tbz-tar-bunzip2 \
                               --hint=perl-Archive-Extract-tgz-tar-gzip \
                               --hint=perl-Archive-Extract-txz-tar-unxz \
                               --hint=perl-Archive-Extract-xz-unxz \
                               --hint=perl-Archive-Extract-zip-unzip \
                               --hint=perl-Archive-Extract-Z-uncompress \
                               --hint=rubygem-minitest \
                               --hint=rubygem-rspec \
                               --hint=sendmail \
| tee sampledata/fedora/25/selfhosting-binary-packages-full.txt


cat sampledata/fedora/25/toplevel-binary-packages.txt | xargs \
./whatpkgs.py neededtoselfhost --merge --no-recommends \
                               --no-sources \
                               --hint=coreutils \
                               --hint=cronie-noanacron \
                               --hint=environment-modules \
                               --hint=fedora-logos-httpd \
                               --hint=fedora-release \
                               --hint=glibc-minimal-langpack \
                               --hint=gnuplot \
                               --hint=infinipath-psm \
                               --hint=java-1.8.0-openjdk-javadoc \
                               --hint=kernel-core \
                               --hint=kernel-devel \
                               --hint=libcrypt-nss \
                               --hint=libverto-libev \
                               --hint=perl-Archive-Extract-bz2-bunzip2 \
                               --hint=perl-Archive-Extract-gz-gzip \
                               --hint=perl-Archive-Extract-lzma-Compress-unLZMA \
                               --hint=perl-Archive-Extract-tar-tar \
                               --hint=perl-Archive-Extract-tbz-tar-bunzip2 \
                               --hint=perl-Archive-Extract-tgz-tar-gzip \
                               --hint=perl-Archive-Extract-txz-tar-unxz \
                               --hint=perl-Archive-Extract-xz-unxz \
                               --hint=perl-Archive-Extract-zip-unzip \
                               --hint=perl-Archive-Extract-Z-uncompress \
                               --hint=rubygem-minitest \
                               --hint=rubygem-rspec \
                               --hint=sendmail \
| tee sampledata/fedora/25/selfhosting-binary-packages-short.txt

cat sampledata/fedora/25/selfhosting-binary-packages-short.txt | xargs \
./whatpkgs.py getsourcerpm \
| tee sampledata/fedora/25/selfhosting-source-packages-short.txt

cat sampledata/fedora/25/selfhosting-binary-packages-short.txt | xargs \
./whatpkgs.py getsourcerpm --full-name \
| tee sampledata/fedora/25/selfhosting-source-packages-full.txt

