#!/usr/bin/env python

import os
import shutil
import glob
import kobo.rpmlib
import kobo.shortcuts
import koji
import munch
import logging
from optparse import OptionParser
from kobo.threads import ThreadPool, WorkerThread

logging.basicConfig()
logger=logging.getLogger("koji-bootstrap")
logger.setLevel(logging.DEBUG)

class ImportThread(WorkerThread):
    def process(self, item, num):
        nvr, epoch, total, opts = item
        self.pool.log_info("Downloading %s (%s/%s)" % (nvr, num, total))
        n_retries = 1
        while n_retries <= 3:
            try:
                self.import_build(nvr, epoch, opts)
                if opts.import_dest_tag:
                    self.tag_build(nvr, opts)
                break
            except RuntimeError:
                self.pool.log_error("Retrying import#%d of %s" % (n_retries, nvr))
                continue
            finally:
                n_retries =+ 1

    def tag_build(self, nvr, opts):
        # XXX: use clientsession :-)
        pkg_name = kobo.rpmlib.parse_nvr(nvr)['name']
        self.pool.log_debug("Whitelisting %s into %s" % (pkg_name, opts.import_dest_tag))
        try:
            ret, out = kobo.shortcuts.run("koji --profile '%s' add-pkg --owner %s %s %s" % (opts.koji_dest_profile, opts.import_owner, opts.import_dest_tag, pkg_name))
        except RuntimeError:
            pass

        self.pool.log_debug("Tagging %s into %s" % (nvr, opts.import_dest_tag))
        ret, out = kobo.shortcuts.run("koji --profile '%s' tag-build --nowait %s %s" % (opts.koji_dest_profile, opts.import_dest_tag, nvr))

    def import_build(self, nvr, epoch, opts):
        workdir = os.path.join(opts.workdir, nvr) # store it under $workdir/$build
        shutil.rmtree(workdir, ignore_errors=True)
        os.makedirs(workdir)
        ret, out = kobo.shortcuts.run("koji --profile '%s' download-build %s" % (opts.koji_profile, nvr), workdir=workdir)

        for rpm in glob.glob("%s/*" % workdir):
            self.pool.log_debug("Importing rpm %s" % rpm)
            ret, out = kobo.shortcuts.run("koji --profile '%s' import --create-build --src-epoch '%s' %s" % (opts.koji_dest_profile, epoch, rpm))

        self.pool.log_debug("Removing workdir %s" % workdir)
        shutil.rmtree(workdir, ignore_errors=True)

def get_koji_session(options):
    koji_config = munch.Munch(koji.read_config(
        profile_name=options.koji_profile,
    ))
    #koji_module = koji.get_profile_module(
    #    options.koji_profile,
    #    config=koji_config,
    #    )

    address = koji_config.server
    return koji.ClientSession(address, opts=koji_config)

def get_nevra(data):
    nevra = kobo.rpmlib.parse_nvra(data)
    if nevra['arch'] != 'src':
        nevra = kobo.rpmlib.parse_nvr(data)
    return nevra

def get_nvrs(source):
    nevrs = set()
    fd = open(source, "r")
    for item in fd.readlines():
        item = item.strip()
        nevrs.add(kobo.rpmlib.make_nvr(get_nevra(item)))

    return sorted(list(nevrs))

def handle_pretty_print_nvrs(opts):
    for item in get_nvrs(opts.builds_from_file):
        print (item)

def handle_missing_builds(opts):
    nvrs = get_nvrs(opts.builds_from_file)
    koji_session = get_koji_session(opts)

    for item in nvrs:
        build_info = koji_session.getBuild(item)
        if not build_info:
            print(item)

def handle_import_builds(opts):
    nevrs = set()
    fd = open(opts.builds_from_file, "r")

    # additional implementation due extra need for epoch
    for item in fd.readlines():
        item = item.strip()
        nevra = get_nevra(item)
        nvr = kobo.rpmlib.make_nvr(nevra)
        nevrs.add((nvr, nevra['epoch']))

    pool = ThreadPool(logger=logger)
    for x in xrange(opts.import_threads):
        pool.add(ImportThread(pool))

    pool.start()
    for item in nevrs:
        pool.queue.put((item[0], item[1], len(nevrs), opts))
    pool.stop()

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--builds-from-file")
    parser.add_option("--find-missing-builds", help="Checks whether builds are present in given koji instance",
        action="store_const", const="missing", dest="action")
    parser.add_option("--print-builds", help="Prints builds in a koji-compat format",
        action="store_const", const="print", dest="action")
    parser.add_option("--import-builds", help="Import builds",
        action="store_const", const="import", dest="action")
    parser.add_option("--import-threads",
        help="Import threads (default is 4)", default=6, type=int)
    parser.add_option("--import-dest-tag",
        help="Tag build after import. Requires manual whitelist ...", metavar="TAG")
    parser.add_option("--import-owner",
        help="Owner for koji add-pkg", metavar="USER")

    parser.add_option("--koji-profile", default="koji")
    parser.add_option("--koji-dest-profile", default="koji", help="profile of Koji import-target")
    parser.add_option("--workdir", help="This is required for import of builds", default="/tmp/import")
    parser.add_option("--debug", action="store_true", help="Print debug info such as individual rpm imports")
    opts, args = parser.parse_args()

    if not opts.builds_from_file:
        parser.error("--builds-from-file is required to load input information")

    if not opts.action:
        parser.error("At least one of --import-builds --print-builds --find-missing-builds is needed")
    if opts.import_dest_tag and not opts.import_owner:
        parser.error("You need to specify --import-owner with --import-dest-tag")

    logger.setLevel(logging.INFO)
    if opts.debug:
        logger.setLevel(logging.DEBUG)


    if opts.action == "print":
        handle_pretty_print_nvrs(opts)

    elif opts.action == "missing":
        handle_missing_builds(opts) 
    
    elif opts.action == "import":
        handle_import_builds(opts) 
