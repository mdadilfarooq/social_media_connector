# Define the default target
.DEFAULT_GOAL := help

# Define variables
COMPOSE := docker-compose
COMPOSE_FILE := docker-compose.yaml

# Define targets and their commands
.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Available targets:"
	@echo "  start      Start containers"
	@echo "  stop       Stop containers"

.PHONY: start
start:
	$(COMPOSE) -f $(COMPOSE_FILE) up -d

.PHONY: stop
stop:
	$(COMPOSE) -f $(COMPOSE_FILE) down
