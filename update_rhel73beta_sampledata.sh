#!/bin/bash

set -x #echo on

cat sampledata/rhel/7.3beta/toplevel-binary-packages.txt| xargs \
./whatpkgs.py getsourcerpm --rhel --full-name \
| tee sampledata/rhel/7.3beta/toplevel-source-packages.txt


cat sampledata/rhel/7.3beta/toplevel-binary-packages.txt|xargs \
./whatpkgs.py neededby --rhel --merge --no-recommends \
                       --hint=glibc-minimal-langpack \
                       --hint=fedora-release \
                       --hint=libcrypt-nss \
                       --hint=cronie-noanacron \
                       --hint=coreutils \
| tee sampledata/rhel/7.3beta/runtime-binary-dependency-packages-short.txt


cat sampledata/rhel/7.3beta/toplevel-binary-packages.txt|xargs \
./whatpkgs.py neededby --rhel --merge --no-recommends --full-name \
                       --hint=glibc-minimal-langpack \
                       --hint=fedora-release \
                       --hint=libcrypt-nss \
                       --hint=cronie-noanacron \
                       --hint=coreutils \
| tee sampledata/rhel/7.3beta/runtime-binary-dependency-packages-full.txt


cat sampledata/rhel/7.3beta/runtime-binary-dependency-packages-short.txt| xargs \
./whatpkgs.py getsourcerpm --rhel \
| tee sampledata/rhel/7.3beta/runtime-source-packages-short.txt


cat sampledata/rhel/7.3beta/runtime-binary-dependency-packages-short.txt| xargs \
./whatpkgs.py getsourcerpm --rhel --full-name \
| tee sampledata/rhel/7.3beta/runtime-source-packages-full.txt


cat sampledata/rhel/7.3beta/runtime-binary-dependency-packages-short.txt | xargs \
./whatpkgs.py neededtoselfhost --rhel --merge --no-recommends \
                               --no-sources \
                               --hint=glibc-minimal-langpack \
                               --hint=fedora-release \
                               --hint=libcrypt-nss \
                               --hint=cronie-noanacron \
                               --hint=coreutils \
                               --hint=java-1.8.0-openjdk-devel \
                               --hint=java-1.8.0-openjdk-javadoc \
                               --hint=sendmail \
                               --hint=environment-modules \
                               --hint=fedora-logos-httpd \
                               --hint=rubygem-minitest \
                               --hint=rubygem-rspec \
                               --hint=kernel-core \
                               --hint=gnuplot \
                               --hint=perl-Archive-Extract-lzma-Compress-unLZMA \
                               --hint=perl-Archive-Extract-tgz-tar-gzip \
                               --hint=perl-Archive-Extract-Z-uncompress \
                               --hint=perl-Archive-Extract-bz2-bunzip2 \
                               --hint=perl-Archive-Extract-gz-gzip \
                               --hint=perl-Archive-Extract-tar-tar \
                               --hint=perl-Archive-Extract-txz-tar-unxz \
                               --hint=perl-Archive-Extract-zip-unzip \
                               --hint=perl-Archive-Extract-tbz-tar-bunzip2 \
                               --hint=perl-Archive-Extract-xz-unxz \
                               --hint=infinipath-psm \
                               --hint=xorg-x11-xinit \
| tee sampledata/rhel/7.3beta/selfhosting-binary-packages-short.txt


cat sampledata/rhel/7.3beta/runtime-binary-dependency-packages-short.txt | xargs \
./whatpkgs.py neededtoselfhost --rhel --merge --no-recommends --full-name \
                               --no-sources \
                               --hint=glibc-minimal-langpack \
                               --hint=fedora-release \
                               --hint=libcrypt-nss \
                               --hint=cronie-noanacron \
                               --hint=coreutils \
                               --hint=java-1.8.0-openjdk-devel \
                               --hint=java-1.8.0-openjdk-javadoc \
                               --hint=sendmail \
                               --hint=environment-modules \
                               --hint=fedora-logos-httpd \
                               --hint=rubygem-minitest \
                               --hint=rubygem-rspec \
                               --hint=kernel-core \
                               --hint=gnuplot \
                               --hint=perl-Archive-Extract-lzma-Compress-unLZMA \
                               --hint=perl-Archive-Extract-tgz-tar-gzip \
                               --hint=perl-Archive-Extract-Z-uncompress \
                               --hint=perl-Archive-Extract-bz2-bunzip2 \
                               --hint=perl-Archive-Extract-gz-gzip \
                               --hint=perl-Archive-Extract-tar-tar \
                               --hint=perl-Archive-Extract-txz-tar-unxz \
                               --hint=perl-Archive-Extract-zip-unzip \
                               --hint=perl-Archive-Extract-tbz-tar-bunzip2 \
                               --hint=perl-Archive-Extract-xz-unxz \
                               --hint=infinipath-psm \
                               --hint=xorg-x11-xinit \
| tee sampledata/rhel/7.3beta/selfhosting-binary-packages-full.txt


cat sampledata/rhel/7.3beta/runtime-binary-dependency-packages-short.txt | xargs \
./whatpkgs.py neededtoselfhost --rhel --merge --no-recommends \
                               --sources \
                               --hint=glibc-minimal-langpack \
                               --hint=fedora-release \
                               --hint=libcrypt-nss \
                               --hint=cronie-noanacron \
                               --hint=coreutils \
                               --hint=java-1.8.0-openjdk-devel \
                               --hint=java-1.8.0-openjdk-javadoc \
                               --hint=sendmail \
                               --hint=environment-modules \
                               --hint=fedora-logos-httpd \
                               --hint=rubygem-minitest \
                               --hint=rubygem-rspec \
                               --hint=kernel-core \
                               --hint=gnuplot \
                               --hint=perl-Archive-Extract-lzma-Compress-unLZMA \
                               --hint=perl-Archive-Extract-tgz-tar-gzip \
                               --hint=perl-Archive-Extract-Z-uncompress \
                               --hint=perl-Archive-Extract-bz2-bunzip2 \
                               --hint=perl-Archive-Extract-gz-gzip \
                               --hint=perl-Archive-Extract-tar-tar \
                               --hint=perl-Archive-Extract-txz-tar-unxz \
                               --hint=perl-Archive-Extract-zip-unzip \
                               --hint=perl-Archive-Extract-tbz-tar-bunzip2 \
                               --hint=perl-Archive-Extract-xz-unxz \
                               --hint=infinipath-psm \
                               --hint=xorg-x11-xinit \
| tee sampledata/rhel/7.3beta/selfhosting-source-packages-short.txt


cat sampledata/rhel/7.3beta/runtime-binary-dependency-packages-short.txt | xargs \
./whatpkgs.py neededtoselfhost --rhel --merge --no-recommends --full-name \
                               --sources \
                               --hint=glibc-minimal-langpack \
                               --hint=fedora-release \
                               --hint=libcrypt-nss \
                               --hint=cronie-noanacron \
                               --hint=coreutils \
                               --hint=java-1.8.0-openjdk-devel \
                               --hint=java-1.8.0-openjdk-javadoc \
                               --hint=sendmail \
                               --hint=environment-modules \
                               --hint=fedora-logos-httpd \
                               --hint=rubygem-minitest \
                               --hint=rubygem-rspec \
                               --hint=kernel-core \
                               --hint=gnuplot \
                               --hint=perl-Archive-Extract-lzma-Compress-unLZMA \
                               --hint=perl-Archive-Extract-tgz-tar-gzip \
                               --hint=perl-Archive-Extract-Z-uncompress \
                               --hint=perl-Archive-Extract-bz2-bunzip2 \
                               --hint=perl-Archive-Extract-gz-gzip \
                               --hint=perl-Archive-Extract-tar-tar \
                               --hint=perl-Archive-Extract-txz-tar-unxz \
                               --hint=perl-Archive-Extract-zip-unzip \
                               --hint=perl-Archive-Extract-tbz-tar-bunzip2 \
                               --hint=perl-Archive-Extract-xz-unxz \
                               --hint=infinipath-psm \
                               --hint=xorg-x11-xinit \
| tee sampledata/rhel/7.3beta/selfhosting-source-packages-full.txt
