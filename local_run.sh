#!/bin/sh
git pull origin master
export TESSDATA_PREFIX=/Users/andres/dev/crypto_auto/tessdata
export guard_key="$(cat filekey.key)"
python order_executor.py
