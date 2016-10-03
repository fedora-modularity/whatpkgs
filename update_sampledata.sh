#!/bin/bash

set -x #echo on

cat sampledata/toplevel-binary-packages.txt| xargs \
./whatpkgs.py getsourcerpm --full-name \
| tee sampledata/toplevel-source-packages.txt


cat sampledata/toplevel-binary-packages.txt|xargs \
./whatpkgs.py neededby --merge --no-recommends \
                       --hint=glibc-minimal-langpack \
                       --hint=fedora-release \
                       --hint=libcrypt-nss \
                       --hint=cronie-noanacron \
                       --hint=coreutils \
| tee sampledata/runtime-binary-dependency-packages-short.txt


cat sampledata/toplevel-binary-packages.txt|xargs \
./whatpkgs.py neededby --merge --no-recommends --full-name \
                       --hint=glibc-minimal-langpack \
                       --hint=fedora-release \
                       --hint=libcrypt-nss \
                       --hint=cronie-noanacron \
                       --hint=coreutils \
| tee sampledata/runtime-binary-dependency-packages-full.txt


cat sampledata/runtime-binary-dependency-packages-short.txt| xargs \
./whatpkgs.py getsourcerpm \
| tee sampledata/runtime-source-packages-short.txt


cat sampledata/runtime-binary-dependency-packages-short.txt| xargs \
./whatpkgs.py getsourcerpm --full-name \
| tee sampledata/runtime-source-packages-full.txt


cat sampledata/runtime-binary-dependency-packages-short.txt | xargs \
./whatpkgs.py neededtoselfhost --merge --no-recommends \
                               --no-sources \
                               --hint=glibc-minimal-langpack \
                               --hint=fedora-release \
                               --hint=libcrypt-nss \
                               --hint=cronie-noanacron \
                               --hint=coreutils \
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
| tee sampledata/selfhosting-binary-packages-short.txt


cat sampledata/runtime-binary-dependency-packages-short.txt | xargs \
./whatpkgs.py neededtoselfhost --merge --no-recommends --full-name \
                               --no-sources \
                               --hint=glibc-minimal-langpack \
                               --hint=fedora-release \
                               --hint=libcrypt-nss \
                               --hint=cronie-noanacron \
                               --hint=coreutils \
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
| tee sampledata/selfhosting-binary-packages-full.txt


cat sampledata/runtime-binary-dependency-packages-short.txt | xargs \
./whatpkgs.py neededtoselfhost --merge --no-recommends \
                               --sources \
                               --hint=glibc-minimal-langpack \
                               --hint=fedora-release \
                               --hint=libcrypt-nss \
                               --hint=cronie-noanacron \
                               --hint=coreutils \
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
| tee sampledata/selfhosting-source-packages-short.txt


cat sampledata/runtime-binary-dependency-packages-short.txt | xargs \
./whatpkgs.py neededtoselfhost --merge --no-recommends --full-name \
                               --sources \
                               --hint=glibc-minimal-langpack \
                               --hint=fedora-release \
                               --hint=libcrypt-nss \
                               --hint=cronie-noanacron \
                               --hint=coreutils \
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
| tee sampledata/selfhosting-source-packages-full.txt
