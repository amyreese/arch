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

	echo "signing gpg key for jreese@leetcode.net (D53EA311DE6184DC)"
	sudo pacman-key --lsign-key D53EA311DE6184DC
fi

