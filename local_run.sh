#!/bin/sh
git pull origin master
export TESSDATA_PREFIX=tessdata
export guard_key="$(cat filekey.key)"
python order_executor.py
