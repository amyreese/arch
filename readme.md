Noswap Arch Repo
================

This repository contains package builds for my projects and for managing my
machines.  These packages are hosted at https://noswap.com/pub/arch/ and are
available for anyone to install and use.

There are three ways to use the packages contained in this project.  You can
add the noswap repository to your `pacman.conf` and install them by name; you
can download the individual packages and install them manually; or you can
clone this repository and use `makepkg` or the included scripts to build the
packages on your own machine.


Repository
==========

You can add the repository to your `pacman.conf` with the following commands:

    $ wget https://noswap.com/pub/arch/noswap-repo.sh
    $ sudo sh noswap-repo.sh

If you prefer, you can add the repository by hand by adding the following
lines to `/etc/pacman.conf`:

    [noswap]
    Server = https://noswap.com/pub/arch/
    
Make sure that if you manually add the repository, you also import my GPG key:

    $ pacman-key --recv-keys D53EA311DE6184DC
    $ pacman-key --lsign-key D53EA311DE6184DC


License
=======

All package definitions and scripts are copyright (c) 2012 John Reese.
All package definitions and scripts are licensed under the MIT license.
Packaged applications may be licensed differently; see the package
definitions for details.
