#!/bin/bash
docker stop guardrails-server || true
docker rm guardrails-server || true