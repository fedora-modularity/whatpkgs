#!/bin/bash

set -x #echo on

cat sampledata/fedora/26/toplevel-binary-packages.txt| xargs \
./whatpkgs.py getsourcerpm --full-name --version=26 \
| sort | tee sampledata/fedora/26/toplevel-source-packages.txt


cat sampledata/fedora/26/toplevel-binary-packages.txt|xargs \
./whatpkgs.py neededby --merge --no-recommends --version=26 \
                       --hint=coreutils \
                       --hint=cronie-noanacron \
                       --hint=fedora-release \
                       --hint=glibc-minimal-langpack \
                       --hint=libcrypt \
                       --hint=python-libs \
                       --hint=pkgconf-pkg-config \
| sort | tee sampledata/fedora/26/runtime-binary-dependency-packages-short.txt


cat sampledata/fedora/26/toplevel-binary-packages.txt|xargs \
./whatpkgs.py neededby --merge --no-recommends --full-name --version=26 \
                       --hint=coreutils \
                       --hint=cronie-noanacron \
                       --hint=fedora-release \
                       --hint=glibc-minimal-langpack \
                       --hint=libcrypt \
                       --hint=python-libs \
                       --hint=pkgconf-pkg-config \
| sort | tee sampledata/fedora/26/runtime-binary-dependency-packages-full.txt


cat sampledata/fedora/26/runtime-binary-dependency-packages-short.txt| xargs \
./whatpkgs.py getsourcerpm --version=26 \
| sort | tee sampledata/fedora/26/runtime-source-packages-short.txt


cat sampledata/fedora/26/runtime-binary-dependency-packages-short.txt| xargs \
./whatpkgs.py getsourcerpm --full-name --version=26 \
| sort | tee sampledata/fedora/26/runtime-source-packages-full.txt


cat sampledata/fedora/26/toplevel-binary-packages.txt \
    sampledata/fedora/26/selfhosting-overrides.txt | xargs \
./whatpkgs.py neededtoselfhost --merge --no-recommends \
                               --full-name --version=26 \
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
                               --hint=libcrypt \
                               --hint=libverto-libev \
                               --hint=pkgconf-pkg-config \
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
| sort | tee sampledata/fedora/26/selfhosting-binary-packages-full.txt


cat sampledata/fedora/26/toplevel-binary-packages.txt \
    sampledata/fedora/26/selfhosting-overrides.txt | xargs \
./whatpkgs.py neededtoselfhost --merge --no-recommends --version=26 \
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
                               --hint=libcrypt \
                               --hint=libverto-libev \
                               --hint=pkgconf-pkg-config \
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
| sort | tee sampledata/fedora/26/selfhosting-binary-packages-short.txt

cat sampledata/fedora/26/selfhosting-binary-packages-short.txt | xargs \
./whatpkgs.py getsourcerpm --version=26 \
| sort | tee sampledata/fedora/26/selfhosting-source-packages-short.txt

cat sampledata/fedora/26/selfhosting-binary-packages-short.txt | xargs \
./whatpkgs.py getsourcerpm --full-name --version=26 \
| sort | tee sampledata/fedora/26/selfhosting-source-packages-full.txt

