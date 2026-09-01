#!/usr/bin/env bash
# Paste the Web3Forms access key that arrived at info@cli0ck.com:
#   ./set-key.sh 1a2b3c4d-....
set -euo pipefail
[ $# -eq 1 ] || { echo "usage: ./set-key.sh <access-key>"; exit 1; }
cd "$(dirname "$0")"
sed -i "s/^W3F_KEY = .*/W3F_KEY = '$1'/" build/gen.py
python3 build/gen.py > /dev/null
grep -q "$1" contact.html && echo "key wired into contact.html" || { echo "FAILED"; exit 1; }
git add -A
git -c user.email=info@cli0ck.com -c user.name=cli0ck commit -q -m "Wire the contact form access key"
git push -q origin main
echo "pushed — live in about a minute at https://cli0ck.com/contact.html"
