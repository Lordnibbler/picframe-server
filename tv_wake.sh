#!/bin/bash

while true; do
    echo "on 0" | cec-client -s -d 1 >/dev/null 2>&1
    sleep 60
done