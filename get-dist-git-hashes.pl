#!/usr/bin/perl
use strict;
use warnings;
use MCE::Loop;

my $if = shift @ARGV or die "Usage: get-dist-git-hashes.pl <selfhosting-source-packages-full.txt>\n";

my @pkgs;
open my $fh, '<', $if or die "Cannot open '${if}': $!\n";
while (<$fh>) {
    chomp;
    /^\d+:(.+)\.src$/;
    push @pkgs, $1;
}
close $fh or die "Cannot close '${if}': $!\n";

MCE::Loop::init { max_workers => 16 };

mce_loop {
    my ($mce, $cref, $cid) = @_;
    for (@$cref) {
        my $hash;
        for (my $i = 0; $i < 3; $i++) {
            my $output = `koji buildinfo $_`;
            ($hash) = ($output =~ /\/rpms\/[^:]+:([a-f0-9]+)/);
            last if $hash;
        }
        MCE->say($_ . ': ' . ($hash // ''));
    }
} @pkgs;
