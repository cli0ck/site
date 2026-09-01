#!/usr/bin/env bash
# ./set-emailjs.sh <service_id> <template_id> <public_key>
set -euo pipefail
[ $# -eq 3 ] || { echo "usage: ./set-emailjs.sh service_xxx template_xxx PUBLIC_KEY"; exit 1; }
cd "$(dirname "$0")"
sed -i "s|service:  '[^']*'|service:  '$1'|; s|template: '[^']*'|template: '$2'|; s|key:      '[^']*'|key:      '$3'|" assets/contact.js
grep -q "$1" assets/contact.js && grep -q "$3" assets/contact.js || { echo "FAILED to write ids"; exit 1; }
echo "wired: $1 / $2 / ${3:0:6}…"
git add -A
git -c user.email=info@cli0ck.com -c user.name=cli0ck commit -q -m "Send the branded template through EmailJS"
git push -q origin main
echo "pushed — live in about a minute"
