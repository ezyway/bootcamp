#!/usr/env/bin bash

echo 'This script will create 2 docker containers, one with curl and one with nginx. From curl container, it will fetch the index.html and then dump its output to ./output/op.txt file and then remove containers'

# Start containers
echo "Starting Docker containers..."
if ! docker compose up --build; then
    echo "FAILED: Could not start Docker containers - check docker-compose.yml and Docker daemon"
    exit 1
fi
echo "✓ Containers started successfully"


# Also show all container logs for reference
echo "All container logs:"
docker compose logs
echo "✓ All logs displayed"

# Clean up
echo "Cleaning up containers..."
if ! docker compose down; then
    echo "FAILED: Could not stop containers - manually run 'docker compose down'"
    exit 1
fi
echo "✓ Containers cleaned up"

echo "SUCCESS: Docker containers started → curl fetched data → output saved to ./output/op.txt → containers cleaned up"