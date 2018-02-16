.PHONY: all

PYTHON_INTERPRETER=python3.6
DOCKER_ORG=m4ucorp
DOCKER_IMG_NAME=plataformas-awsfinder
VERSION=$(shell cat awsfinder/__version__.py|cut -d" " -f3|sed 's/"//g')

all: venv requirements

venv:
	if [ ! -d "venv/" ]; then virtualenv -p ${PYTHON_INTERPRETER} venv/; fi

requirements:
	./venv/bin/pip3 install -r requirements.txt

docker-build:
	docker build -t ${DOCKER_ORG}/${DOCKER_IMG_NAME}:${VERSION} .

docker-push:
	docker tag ${DOCKER_ORG}/${DOCKER_IMG_NAME}:${VERSION} ${DOCKER_ORG}/${DOCKER_IMG_NAME}:latest
	docker push ${DOCKER_ORG}/${DOCKER_IMG_NAME}:${VERSION}
	docker push ${DOCKER_ORG}/${DOCKER_IMG_NAME}:latest

docker: docker-build docker-push

clean:
	rm -rf venv
