#!/bin/bash

mozparse() {
    url="https://ftp.mozilla.org/pub/mozilla.org/firefox/$1/"

    if [ -z "$2" ]; then
        pattern='>\d+(\.\d)+.*?<'
    else
        pattern=$2
    fi

    curl -s $url | grep -oP $pattern | tr '<>/' ' ' | grep -oP '\S+' | sort -V | tail -n1
}

release=$(mozparse releases)

candidate=$(mozparse candidates '>\d+(\.\d)+-candidates/<')
major=${candidate/-candidates}
build=$(mozparse "candidates/$major-candidates" '>build\d+/<')
rc=${build/build}
rcbuild=${major}rc${rc}

target=$(echo -e "$release\n$rcbuild" | sort -V | tail -n1)

sed -i "s/pkgver=.*/pkgver=${target}/" PKGBUILD
