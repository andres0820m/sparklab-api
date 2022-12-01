#!/bin/sh
git pull origin master
export TESSDATA_PREFIX=/home/andres/Escritorio/bot_pagos/tessdata
export guard_key="$(cat filekey.key)"
python order_executor.py
