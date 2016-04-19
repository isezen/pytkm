#!/usr/bin/env bash

cd /Users/isezen/proj/pytkm
if [ -f tkm.pid ];then
  ps up "$(<tkm.pid)" >/dev/null && echo "Already running" || ./tkm.py -tipaw -o 00 -r 60 &
else
  ./tkm.py -tipaw -o 00 -r 60 &
fi

