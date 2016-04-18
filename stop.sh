#!/usr/bin/env bash

pid=$(pgrep Python ./tkm.py)
kill -15 "$pid"
