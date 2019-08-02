#!/bin/bash
pid=`ps aux | grep 'jupyter-notebook' | grep -v color | awk -F' '  '{ print $2 }'`
kill -9 $pid
