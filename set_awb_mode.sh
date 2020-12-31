#!/bin/bash

# Remove purple image issues with latest firmware

service motion stop
vcdbg set awb_mode 0
service motion start
