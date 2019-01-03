#!/usr/bin/env bash

watchmedo auto-restart -- celery -A celery_worker:celery worker --loglevel=INFO