#!/usr/bin/env bash
set -euo pipefail

trap 'echo "ERROR on Line no: $LINENO";exit 1' ERR

date > file.txt

for i in {a..z}
do
	echo $r >> file.txt && echo $i
done

