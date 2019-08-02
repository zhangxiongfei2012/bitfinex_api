#!/bin/bash
nohup  jupyter notebook --ip=0.0.0.0 --port=8080  > ./jupytrt.out 2>&1 &
