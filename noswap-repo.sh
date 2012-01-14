#!/bin/sh

pac=/etc/pacman.conf

if grep -q "\[archlinuxfr\]" $pac
then
	echo "archlinuxfr repo already added"
else
	echo "adding archlinuxfr repo"
	echo >> $pac
	echo "[archlinuxfr]" >> $pac
	echo "Server = http://repo.archlinux.fr/\$arch" >> $pac
fi

if grep -q "\[noswap\]" $pac
then
	echo "noswap repo already added"
else
	echo "adding noswap repo"
	echo >> $pac
	echo "[noswap]" >> $pac
	echo "Server = http://pub.noswap.com/arch" >> $pac
fi

