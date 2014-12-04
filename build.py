#!/usr/bin/env python3

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile

from functools import lru_cache, partial
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
ARCHROOT = join(BASE, '.archroot')
ARCHROOT_LOCK = join(BASE, '.archroot.lock')
LOCALREPO = join(BASE, '.repo/')
REMOTEREPO = 'liara:/home/jreese/pub/arch/'
DATABASE = 'noswap.db.tar.xz'
USERGROUP = 'jreese:jreese'

CPUARCH = bt('uname -m')
PKGREGEX = "'.*/{0}-\(preview\|latest\|.?[0-9]\).*\.pkg\.tar\.xz.*'"


class ChrootBuild(object):
    def __init__(self, fresh=False, clean=False):
        log.debug('__init__')

        self.pkgroot = join(ARCHROOT, 'packages')
        self.pkgpath = '/packages'
        self.fresh = fresh
        self.cleanup = clean

        self.rsh = partial(sh, 'sudo', 'arch-chroot', ARCHROOT)
        self.rbt = partial(bt, 'sudo', 'arch-chroot', ARCHROOT)

    def __enter__(self):
        log.debug('__enter__')
        self.unmount()
        if self.fresh:
            self.clean()
        self.init()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        log.debug('__exit__')
        self.unmount()
        if self.cleanup:
            self.clean()

    def unmount(self):
        log.info('checking mounts')

        mount_list = bt('mount').split('\n')
        log.debug('current mounts:\n%s\n', '\n'.join(mount_list))

        # make sure the chroot isn't already mounted
        for mount in (
            join(ARCHROOT, 'sys'),
            join(ARCHROOT, 'proc'),
            join(ARCHROOT, 'dev', 'pts'),
            join(ARCHROOT, 'dev'),
            ARCHROOT,
        ):
            for mount_entry in mount_list:
                if mount in mount_entry:
                    log.info('mount point %s found, unmounting', mount)

                    try:
                        sh('sudo umount', mount)
                        break

                    except:
                        log.error('umount failed, listing lsof for %s:', mount)
                        sudo('lsof', mount, '| grep', mount)
                        raise

    def init(self):
        log.debug('Initializing archroot %s', ARCHROOT)

        if not exists(ARCHROOT):
            log.info('Creating new archroot in %s', ARCHROOT)
            try:
                sudo('mkarchroot', ARCHROOT, 'base', 'base-devel')
            except:
                log.exception('mkarchroot returned non-zero, ignoring')

            log.info('Creating arch user with uid 1000')
            self.rsh('useradd -m -u 1000 -U arch')

        if exists(self.pkgroot):
            log.debug('Cleaning old packages from %s', self.pkgroot)
            sudo('rm -r', self.pkgroot)
        sudo('mkdir -p', self.pkgroot)

        log.debug('Adding multilib and noswap repos')
        for script in ['multilib-repo.sh', 'noswap-repo.sh']:
            sudo('cp', script, self.pkgroot)
            self.rbt('sh', join(self.pkgpath, script))

    def clean(self):
        if exists(ARCHROOT):
            log.info('Cleaning up archroot %s', ARCHROOT)

            sudo('rm -r', ARCHROOT)
            sudo('rm', ARCHROOT_LOCK)

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


def build_packages(args, packages):
    completed = set()
    failed = set()

    with ChrootBuild(fresh=args.fresh, clean=args.clean) as chroot:
        for package in packages:
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
                sh('rsync --progress -avz --delete', LOCALREPO, REMOTEREPO)

                completed.add(package)
            except:
                log.exception('Build failed')
                failed.add(package)

    return completed, failed


package_dep_re = re.compile(r'^(.*?)(?:[<>=].*)?$')
@lru_cache()
def package_deps(package):
    pkgbuild = join(package, 'PKGBUILD')
    if not isfile(pkgbuild):
        return []

    try:
        dependencies = bt("sh -c 'source {0} && echo $depends'".format(pkgbuild)).split()
        dependencies = [package_dep_re.sub(r'\1', dep) for dep in dependencies]
        log.debug('Package %s depends on %s', package, dependencies)
        return dependencies
    except:
        return []


def resolve_dependencies(packages):
    queue = list(packages)
    packages = []

    log.debug('Unresolved build order: %s', queue)

    limit = len(queue) + 1
    tries = 0
    while len(queue):
        tries += 1
        if tries >= limit:
            log.error('Could not resolve package dependencies after %d tries,\n'
                      'resolved packages: %s\nunresolved packages: %s',
                      tries, packages, queue)
            return []

        package = queue.pop(0)
        log.debug('checking if %s has any dependencies on %s', package, queue)

        for name in package_deps(package):
            if name in queue:
                log.debug('package %s depends on %s', package, name)
                queue.append(package)
                break

        if package not in queue:
            log.debug('package %s in no dependency lists', package)
            packages.append(package)
            limit = tries + len(queue) + 1

    log.debug('Resolved build order: %s', packages)

    return packages


def main():
    os.nice(2)
    os.putenv('INFAKEROOT', '1')

    parser = argparse.ArgumentParser(description='Build packages')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='debug output')
    parser.add_argument('--fresh', action='store_true', default=False,
                        help='force creating a fresh archroot')
    parser.add_argument('--clean', action='store_true', default=False,
                        help='cleanup archroot after running builds')
    parser.add_argument('--retry', type=int, default=None,
                        help='specify the number of retries to attempt')
    parser.add_argument('packages', metavar='PACKAGE', type=str, nargs='*',
                        help='list of package names to build')

    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    try:
        if os.getuid():
            log.debug('Requesting sudo access')
            sh('sudo true')

        log.debug('Syncing local repository from remote')
        sh('rsync --progress -avz --delete', REMOTEREPO, LOCALREPO)

        finished = set()
        failed = set()
        waiting = resolve_dependencies(set(args.packages))

        retry = 0
        while ((args.retry is None and retry <= len(waiting))
                or (args.retry is not None and retry <= args.retry)):
            retry += 1

            completed, failed = build_packages(args, waiting)
            finished |= completed
            for package in completed:
                waiting.remove(package)

            log.info('--- Pass %d ---', retry)

            if completed:
                log.info('Completed: %s', ', '.join(completed))
            if failed:
                log.info('Failed: %s', ', '.join(failed))

            args.fresh = False

        if args.packages:
            log.info('--- Results ---')
        if finished:
            log.info('Builds completed: %s', ', '.join(finished))
        if failed:
            log.info('Builds failed: %s', ', '.join(failed))
            sys.exit(-1)

    except Exception as e:
        if args.debug:
            log.exception('Build generated exception')
        else:
            log.error(e)


if __name__ == '__main__':
    main()

