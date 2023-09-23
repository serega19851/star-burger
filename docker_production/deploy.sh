#!/bin/bash

set -e
cd ..
mkdir -p static
mkdir -p media
git pull

cd docker_production
docker-compose build
docker-compose pull && docker-compose up -d

echo Deploy Docker was successful
