#!/bin/bash

docker build --force-rm -t docker.ill.fr/scientific-software/mdanse:$1 -f $2/Dockerfile .

