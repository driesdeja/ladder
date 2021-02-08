FROM python:3.8.3

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

RUN python -m pip install --upgrade pip

RUN  pip install pipenv

COPY . /ladder/

WORKDIR /ladder

RUN pipenv install --system --deploy --ignore-pipfile


