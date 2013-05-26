#!/usr/bin/env python3

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile

from functools import partial
from os import path

def sh(*command, **kwargs):
    return subprocess.check_call(' '.join(command), shell=True, **kwargs)

def bt(*command, **kwargs):
    return subprocess.check_output(' '.join(command), shell=True, **kwargs).strip()

LOCALREPO = ".repo/"
REMOTEREPO = "liara:/home/jreese/pub/arch/"
DATABASE = "noswap.db.tar.xz"

CPUARCH = bt('uname -m')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

log = logging.getLogger(__name__)
log.addHandler(ch)
log.setLevel(logging.INFO)

class ChrootBuild(object):
    def __init__(self, root=None, fresh=False, clean=False):
        log.debug('__init__')

        if not root:
            root = '.archroot'

        self.root = root
        self.pkgroot = path.join(self.root, 'packages')
        self.fresh = fresh
        self.cleanup = clean

        self.rsh = partial(sh, 'arch-chroot', self.root)
        self.rbt = partial(bt, 'arch-chroot', self.root)

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

        if not path.exists(self.root):
            log.info('Creating new archroot in %s', self.root)
            sh('mkarchroot', self.root, 'base', 'base-devel')

        if path.exists(self.pkgroot):
            log.debug('Cleaning old packages from %s', self.pkgroot)
            shutil.rmtree(self.pkgroot)
        os.makedirs(self.pkgroot)

        log.debug('Adding multilib and noswap repos')
        for script in ['multilib-repo.sh', 'noswap-repo.sh']:
            shutil.copy(script, self.pkgroot)
            self.rbt('sh', path.join('/packages', script))

    def clean(self):
        if path.exists(self.root):
            log.info('Cleaning up archroot %s', self.root)
            shutil.rmtree(self.root)

if __name__ == '__main__':

    if os.getuid():
        args = ['sudo'] + sys.argv
        os.execvp(args[0], args)
        assert False, 'execvp failed!'

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

    with ChrootBuild(root=args.root, fresh=args.fresh, clean=args.clean) as chroot:
        pass
        #chroot.build(packages)
