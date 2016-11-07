#!/usr/bin/env bash

uwsgi --socket 0.0.0.0:5001 \
    --protocol=http \
    --http-chunked-input \
    -w mixmatch.wsgi \
    --master \
    --processes 4 \
    --threads 2
