FROM python:3.9
WORKDIR /reservoirs_web
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY ./web .
