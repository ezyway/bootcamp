#!/usr/bin/env bash
set -euo pipefail

trap 'echo "ERROR on Line no: $LINENO";exit 1' ERR

date > file.txt

echo {a..z}

echo {a..z} >> file.txt
