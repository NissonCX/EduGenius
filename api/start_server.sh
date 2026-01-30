#!/bin/bash
cd "$(dirname "$0")"
nohup /usr/local/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /Users/nissoncx/code/EduGenius/backend.log 2>&1 &
