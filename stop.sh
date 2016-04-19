#!/usr/bin/env bash

cd /Users/isezen/proj/pytkm
if [ -f tkm.pid ];then
  pid="$(<tkm.pid)"
  kill -15 "$pid"
fi

