#!/bin/bash

set -e

cd /opt1/star-burger/

git pull

source venv/bin/activate

pip install -r requirements.txt

npm ci --include=dev

./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

python manage.py collectstatic --noinput
python manage.py migrate --noinput

systemctl restart star-burger.service
systemctl reload nginx.service
systemctl start starburger-clearsessions.service starburger-clearsessions.timer

if [[ -f .env ]]; then
    source .env
fi

access_token=$ROLLBAR_ACCESS_TOKEN

last_commit=$(git rev-parse HEAD)

curl -H "X-Rollbar-Access-Token: $access_token" \
     -H "Content-Type: application/json" \
     -X POST 'https://api.rollbar.com/api/1/deploy' \
     -d '{"environment": "production", "revision": "'${last_commit}'", "rollbar_name": "star-burger", "local_username": "serega19851", "status": "succeeded"}'
echo Deploy was successful
