#!/usr/bin/env bash


echo "Waiting for mysql..."

while ! nc -z db 3306; do
  sleep 0.1
done

echo "MySql started"

#flask db downgrade

if [[ -d "migrations" ]]; then
    flask db migrate
else
    flask db init
    flask db migrate
fi

flask db upgrade

flask run -h 0.0.0.0