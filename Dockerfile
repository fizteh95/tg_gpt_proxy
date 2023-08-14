FROM python:3.11.4-alpine3.18

COPY requirements.txt /tmp/
# git sqlite3 libpq-dev libpq5 gcc g++
RUN apk update && apk add bash
# RUN apk add gcc g++
RUN apk add gcompat
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /src
COPY src/ /src/src/
COPY main.py alembic.ini setup.cfg /src/
COPY so/ /src/so/
COPY tests/ /tests/

WORKDIR /src

EXPOSE 8080
HEALTHCHECK --interval=5s --timeout=5s --retries=5 --start-period=5s CMD curl -f 0.0.0.0:8080/healthcheck || exit 1
