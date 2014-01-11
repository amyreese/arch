#!/usr/bin/env python3

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile

from functools import partial
from os.path import abspath, basename, dirname, exists, isdir, isfile, join

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

log = logging.getLogger(__name__)
log.addHandler(ch)
log.setLevel(logging.INFO)

def sh(*command, **kwargs):
    log.debug('shell: %s', ' '.join(command))
    return subprocess.check_call(' '.join(command), shell=True, **kwargs)
sudo = partial(sh, 'sudo')

def bt(*command, **kwargs):
    log.debug('shell: %s', ' '.join(command))
    out = subprocess.check_output(' '.join(command), shell=True, **kwargs)
    return out.strip().decode()

BASE = os.getcwd()
LOCALREPO = '.repo/'
REMOTEREPO = 'liara:/home/jreese/pub/arch/'
DATABASE = 'noswap.db.tar.xz'
USERGROUP = 'jreese:jreese'

CPUARCH = bt('uname -m')
PKGREGEX = "'.*/{0}-\(latest\|.?[0-9]\).*\.pkg\.tar\.xz.*'"

class ChrootBuild(object):
    def __init__(self, root=None, fresh=False, clean=False):
        log.debug('__init__')

        if not root:
            root = '.archroot'

        self.root = root
        self.pkgroot = join(self.root, 'packages')
        self.pkgpath = '/packages'
        self.fresh = fresh
        self.cleanup = clean

        self.rsh = partial(sh, 'sudo', 'arch-chroot', self.root)
        self.rbt = partial(bt, 'sudo', 'arch-chroot', self.root)

    def __enter__(self):
        log.debug('__enter__')
        if self.fresh:
            self.clean()
        self.init()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        log.debug('__exit__')
        if self.cleanup:
            self.clean()

    def init(self):
        log.debug('Initializing archroot %s', self.root)

        if not exists(self.root):
            log.info('Creating new archroot in %s', self.root)
            sudo('mkarchroot', self.root, 'base', 'base-devel')

        if exists(self.pkgroot):
            log.debug('Cleaning old packages from %s', self.pkgroot)
            sudo('rm -r', self.pkgroot)
        sudo('mkdir -p', self.pkgroot)

        log.debug('Adding multilib and noswap repos')
        for script in ['multilib-repo.sh', 'noswap-repo.sh']:
            sudo('cp', script, self.pkgroot)
            self.rbt('sh', join(self.pkgpath, script))

    def clean(self):
        if exists(self.root):
            log.info('Cleaning up archroot %s', self.root)
            sudo('rm -r', self.root)
            sudo('rm', self.root + '.lock')

    def build(self, package):
        if not isdir(package):
            raise Exception('Package {0} not found'.format(package))
        sh('chmod -R a+rX', package)

        log.debug('Updating pacman')
        self.rsh('pacman -Sy')

        runroot = join(self.pkgroot, 'run.sh')
        runpath = join(self.pkgpath, 'run.sh')
        pkgroot = join(self.pkgroot, package)
        pkgpath = join(self.pkgpath, package)
        command = 'cd {0} && makepkg --asroot -s --noconfirm'.format(pkgpath)

        try:
            sh('grep arch=', join(package, 'PKGBUILD'), '| grep -q any')
            arch = 'any'
        except:
            arch = CPUARCH
        log.debug('Package arch: %s', arch)

        log.debug('Copying sources to archroot')
        sudo('cp -r', package, pkgroot)

        with open('run.sh', 'w') as f:
            f.write(command + '\n')
        sudo('mv', 'run.sh', runroot)

        log.debug('Building: `%s`', command)
        self.rsh('sh', runpath)

        pkgfile = bt('find', pkgroot, '-maxdepth 1 -iregex', PKGREGEX.format(package))
        log.debug('Built package file "%s"', pkgfile)

        return pkgfile

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Build packages')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='debug output')
    parser.add_argument('--root', type=str, default=None,
                        help='root directory of existing archroot')
    parser.add_argument('--fresh', action='store_true', default=False,
                        help='force creating a fresh archroot')
    parser.add_argument('--clean', action='store_true', default=False,
                        help='cleanup archroot after running builds')
    parser.add_argument('packages', metavar='PACKAGE', type=str, nargs='*',
                        help='list of package names to build')

    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    if os.getuid():
        log.debug('Requesting sudo access')
        sh('sudo true')

    log.debug('Syncing local repository from remote')
    sh('rsync -avz --delete', REMOTEREPO, LOCALREPO)

    completed = set()
    failed = set()

    with ChrootBuild(root=args.root, fresh=args.fresh, clean=args.clean) as chroot:
        for package in args.packages:
            try:
                os.chdir(BASE)

                log.info('--- %s ---', package)

                pkgfile = chroot.build(package)
                pkg = basename(pkgfile)

                log.debug('Deleting old package from repository')
                sh('find', LOCALREPO, '-iregex', PKGREGEX.format(package),
                   '-delete')

                log.debug('Copying new package to repository')
                shutil.copy(pkgfile, LOCALREPO)

                os.chdir(LOCALREPO)

                log.info('Signing package')
                sh('gpg --detach-sign ', pkg)

                log.info('Updating database')
                sh('repo-add --sign --verify', DATABASE, '-f', pkg)

                os.chdir(BASE)

                log.debug('Syncing local repository to remote')
                sh('rsync -avz --delete', LOCALREPO, REMOTEREPO)

                completed.add(package)
            except:
                log.exception('Build failed')
                failed.add(package)

    if args.packages:
        log.info('--- Results ---')
    if completed:
        log.info('Builds completed: %s', ', '.join(completed))
    if failed:
        log.info('Builds failed: %s', ', '.join(failed))
        sys.exit(-1)
