FROM python:3.8.2
MAINTAINER driesdeja@gmail.com

COPY ./ /ladder

WORKDIR /ladder

RUN pip install -r requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

