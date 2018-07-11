#!/bin/bash

if [ $# -eq 0 ]; then
  echo "Usage: $0 [\"command\"]"
  exit 0
fi

for i in $(seq 1 8); do
  ssh futebol@rack"${i}" -t "${1}"
done
