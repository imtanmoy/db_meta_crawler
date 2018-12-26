#!/usr/bin/env bash

celery -A celery_worker:celery worker --loglevel=INFO