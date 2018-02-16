FROM python:3.6-slim

RUN mkdir /app
WORKDIR /app

COPY . /app/

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "/app/awsfinder/__main__.py"]
CMD ["--help"]