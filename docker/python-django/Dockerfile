FROM python:3.8.3
MAINTAINER driesdeja@gmail.com

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

RUN python -m pip install --upgrade pip

RUN  pip install pipenv

COPY ./Pipfile.lock /ladder/Pipfile.lock

WORKDIR /ladder

RUN pwd

RUN pipenv install --system --deploy --ignore-pipfile



# COPY ./requirements.txt .

