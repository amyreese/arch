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

