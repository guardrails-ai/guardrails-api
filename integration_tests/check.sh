#!/bin/bash

up="F"
for i in {1..30}; do
if docker exec guardrails-server curl -s http://localhost:8000/; then
    echo "Server is up!"
    up="T"
    break
fi
echo "Waiting for server..."
sleep 5
done

if [ "T" != "${up}" ];
    then
        echo "Server never started!"
        exit 1
fi