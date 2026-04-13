#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a git repository" >&2
  exit 1
fi

echo "== Unique emails in repo history =="
git log --all --format='%ae%n%ce' \
  | sed '/^$/d' \
  | sort \
  | uniq -c \
  | sort -nr

echo

echo "== Unique identities (tungns75 + bantot2006@gmail.com) in repo history =="
git log --all --format='%an <%ae>%n%cn <%ce>' \
  | sed '/^$/d' \
  | sort \
  | uniq -c \
  | sort -nr
