#!/bin/bash

moz="https://ftp.mozilla.org/pub/mozilla.org/firefox"

mozparse() {
    url="$moz/$1/"

    if [ -z "$2" ]; then
        pattern='>\d+(\.\d)+.*?<'
    else
        pattern=$2
    fi

    curl -s $url | grep -oP $pattern | tr '<>/' ' ' | grep -oP '\S+' | sort -V | tail -n1
}

checksums() {
    url="$moz/$1/MD5SUMS"

    curl -s $url | grep en-US | grep .tar.bz2 > md5sums
    sed -i -e "s/md5sums_i686=.*/md5sums_i686=('$(awk '/linux-i686/{print $1}' md5sums)')/" PKGBUILD
    sed -i -e "s/md5sums_x86_64=.*/md5sums_x86_64=('$(awk '/linux-x86_64/{print $1}' md5sums)')/" PKGBUILD
    rm md5sums
}

release=$(mozparse releases)

candidate=$(mozparse candidates '>\d+(\.\d)+-candidates/<')
major=${candidate/-candidates}
build=$(mozparse "candidates/$major-candidates" '>build\d+/<')
rc=${build/build}
rcbuild=${major}rc${rc}

target=$(echo -e "$release\n$rcbuild" | sort -V | tail -n1)

sed -i "s/pkgver=.*/pkgver=${target}/" PKGBUILD

if [ "$target" == "$release" ]
then
    checksums releases/$release
else
    checksums candidates/$candidate/$build
fi
