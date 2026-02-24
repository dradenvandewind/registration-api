sed -i '/SECRET_KEY/d' .env
docker compose run --rm setup >> .env
