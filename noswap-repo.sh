#!/bin/sh

pac=/etc/pacman.conf

if grep -q "\[noswap\]" $pac
then
	echo "noswap repo already added"
else
	echo "adding noswap repo"
	echo >> $pac
	echo "[noswap]" >> $pac
	echo "Server = http://pub.noswap.com/arch" >> $pac

fi

echo "importing and signing gpg key for jreese@leetcode.net (D53EA311DE6184DC)"
pacman-key --recv-keys D53EA311DE6184DC
pacman-key --lsign-key D53EA311DE6184DC

