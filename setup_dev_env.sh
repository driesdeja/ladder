#!/bin/sh
export DEBUG=1

export SECRET_KEY=foo
export DJANGO_ALLOWED_HOSTS="localhost 127.0.0.1 [::1]"


export DB_USER=ladder_user
export DB_PASSWORD=ladder_user_password
export DB_NAME=ladder

export SQL_ENGINE=django.db.backends.postgresql
export SQL_DATABASE=ladder
export SQL_USER=ladder_user
export SQL_PASSWORD=ladder_user_password
export SQL_HOST=localhost
export SQL_PORT=5432

echo "The development environment has been set up!"
