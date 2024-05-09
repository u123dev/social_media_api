FROM python:3.12-alpine
LABEL maintainer="u123@ua.fm"

ENV PYTHONUNBUFFERED 1

WORKDIR app/

COPY requirements.txt ./
RUN pip install -r  requirements.txt
COPY . .

RUN mkdir -p /media

RUN adduser \
    --disabled-password\
    --no-create-home\
    social-user

RUN chown -R social-user /media/
RUN chmod -R 755 /media

USER social-user
