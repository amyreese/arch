#!/bin/sh

pac=/etc/pacman.conf

if grep -q "^\[multilib\]" $pac
then
	echo "multilib repo already enabled"
else
	echo "adding multilib repo"
	echo >> $pac
	echo "[multilib]" >> $pac
	echo "Include = /etc/pacman.d/mirrorlist" >> $pac
fi

