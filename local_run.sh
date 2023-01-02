#!/bin/sh
git pull origin master
export TESSDATA_PREFIX=tessdata
export guard_key="$(cat filekey.key)"
sudo adb start-server
python order_executor.py &
python ads_executor.py
wait
