#!/bin/bash
export PATH=$PATH:/var/task/vendored:/var/runtime:/opt/python:/var/task/venv/bin
export PYTHONPATH=$PYTHONPATH:/var/task/venv/lib/python3.11/site-packages:/var/task/vendored:/var/runtime:/opt/python
python formsg_webhook.py