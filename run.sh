#!/bin/bash
python telegram_board.py &
python order_executor.py &
wait