#!/bin/bash
shipnames=($(ls data/json/ships/*))
for s in "${shipnames[@]}"
do
  echo "$s"
  s=$(basename $s)
  s="${s%.*}"
  python base.py data/json/ships/$s.json > data/ships/$s.md
done
