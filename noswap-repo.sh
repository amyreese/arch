#!/bin/sh

pac=/etc/pacman.conf

if grep -q "\[noswap\]" $pac
then
	echo "noswap repo already added"
else
	echo "adding noswap repo"
	echo >> $pac
	echo "[noswap]" >> $pac
	echo "Server = https://noswap.com/pub/arch" >> $pac

fi

echo "importing and signing gpg key for jreese@leetcode.net (D53EA311DE6184DC)"
pacman-key --add - <<EOM
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v2

mQGiBEe/olYRBACVdv6CEyeShbPUPZYnf6+l6sqaTHNAupf6YdGgJKN7mq9reern
wmTvgxaI6RJ1KFMnR5QMoM8OJJx+uZKpabd7KGm5KKhhWGK9dNK0Rh+1J8m6j859
n/3B/oa/nVU6+x8u9bob4QiccnT/iyuO9TbTRQAGf99unuz3ZJlgMRfcwwCg9IWB
52F2Ior9WEgw4x4DSHIS6EMD/iycV7jHAMVA27iWs+FrFzkoKGU4mTELwpugZpym
bet8eWlldwvZpYxGBatsVEUKDyAiIx3mTTEFn3bh3vY+R8q6gZRAatQ1sQlA9LjE
r4G6pTQkZjq9Y0X6q/FMW1G/qSqzk4ocagy4C9LvBGnf2nhvMoUL9gJ8InX1L5Ud
G5G4A/9Ztl6w5rhwLmVQh1Wjy3bNcfRtOmzJ8pcramy8p4ay3ku6DiIdTPRP+zks
nB+1BBkqFdBmOdKmTY2olYe7Y7VVkKIfjjwgmXmlMjNowTX1tjJmEKGNG0msGtdz
TOYXDTi72HC0P1UKSnTVwxoOrCp+J7S81leeKGs/6bqj8OFiEbQvSm9obiBSZWVz
ZSAoTGVldENvZGUubmV0KSA8anJlZXNlQGxlZXRjb2RlLm5ldD6IYAQTEQIAIAUC
R7+iVgIbAwYLCQgHAwIEFQIIAwQWAgMBAh4BAheAAAoJENU+oxHeYYTcFvcAoNVN
1yzrNWGLKNu6bSEhIlIsOLDRAJ9TfyO9kF2A1PrjWJRmTbMsNre0mrQgSm9obiBS
ZWVzZSA8anJlZXNlQGxlZXRjb2RlLm5ldD6IYAQTEQIAIAUCST7GlgIbAwYLCQgH
AwIEFQIIAwQWAgMBAh4BAheAAAoJENU+oxHeYYTcX2sAoISYx5Pqvhs+KxILb/3y
pl/qod/1AKDo3qKJ2n6Emax6PjX8fkLh6JsQ7LkCDQRHv6JcEAgAs84NghxANuSk
9WVnc/pLPb0qRh09r1x0yofaNele+zHU3oawmtY7emlBWzCg0k1bUKdFeVGJmCeR
RZwNv+QXaKI1BUXIfU7kuvR3uzXaEHPRlOzy2+ggf1j3IkqZc5j0Nb8A8Tb7MfOh
nEYPxOdsCedhVsTbxley1Tm1lasE4FvWyc0GsoL0+AietJ6twrRpSHv4u9UvwyLU
wEow3WEZmUS6BOv8S/rET7iSmhe+ahhASU3PNKO3R7JzA5UaxIK0DCV1tjzN3cSs
E3R5CaErfiOGtolmeIa60kB3mIDYC395OpiBpT8d3qzWFdg+I3kwyVX2Jejo4vKX
qMbADFse4wADBgf+KMxtu1Mq9l5rbqf09dYOIKHRcWA896OiY56SMCaUHJ3C0n9/
XA2FMx6KXfzCt87roKPDV+TOYzW1I+NtuAxMkVzRXi5nrsXXE6UMJcNXugIVKpMd
i5UAzJqHxRl/yVi1NF68w5oQVnXnWg55iRGs8eMKlbiD1di2zEUWJefcCAOnz1wT
YgPYuswipXfH8AfJzqmYgfajtPpFsusLwIvhZ6x4VJrxx1gi9E5ZshsqcFl483Hd
Qez3CbPB2Qk4UnVPh1wgl1cA+d4McjIfE7/7KPvkSCrM4Tcu9SWipYhDaOY0HiJe
ncw2pU/99FwQ55Ymxq0L8nRFGlK3nPe/VdLoKIhJBBgRAgAJBQJHv6JcAhsMAAoJ
ENU+oxHeYYTc78sAn2xPZuwk+/L2wprnf7hlgmsCXXecAJ0X+Uig2VLUNNfr3tau
tWgrfo+yag==
=WVs6
-----END PGP PUBLIC KEY BLOCK-----
EOM
pacman-key --lsign-key D53EA311DE6184DC

sleep 1

