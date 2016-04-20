#!/usr/bin/env bash

cd /Users/isezen/proj/pytkm

pname='tkm.py -tipaw -o 00 -r 60'
grep_query="/usr/bin/grep -i '$pname'"
cmd="/bin/ps -a | $grep_query | /usr/bin/grep -v 'grep' | awk '{print \$1}'"
pid=$(eval "$cmd")
[ -n "$pid" ] && kill -15 "$pid"
