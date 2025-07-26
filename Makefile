# Backend Makefile

DOCKER_HUB_ORG := watkinslabs
IMAGE_NAME := temuragi_backend
VERSION := $(shell cat VERSION)
BUILDER_NAME := temuragi-builder
PLATFORMS := linux/amd64

.PHONY: build push build-push setup-buildx clean help

help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  build       Build Docker image locally"
	@echo "  push        Push image to Docker Hub"
	@echo "  build-push  Build and push in one step"
	@echo "  clean       Remove local images"

setup-buildx:
	@if ! docker buildx ls | grep -q "^$(BUILDER_NAME)"; then \
		echo "Creating buildx builder: $(BUILDER_NAME)"; \
		docker buildx create --name $(BUILDER_NAME) --driver docker-container --bootstrap; \
	fi
	@docker buildx use $(BUILDER_NAME)

build: setup-buildx
	docker buildx build \
		--build-arg VERSION=$(VERSION) \
		-f Dockerfile \
		-t $(DOCKER_HUB_ORG)/$(IMAGE_NAME):$(VERSION) \
		-t $(DOCKER_HUB_ORG)/$(IMAGE_NAME):latest \
		--load \
		.

push:
	@if ! docker info 2>/dev/null | grep -q "Username"; then \
		echo "Not logged into Docker Hub. Please run: docker login"; \
		exit 1; \
	fi
	docker push $(DOCKER_HUB_ORG)/$(IMAGE_NAME):$(VERSION) 
	docker push $(DOCKER_HUB_ORG)/$(IMAGE_NAME):latest

build-push: setup-buildx
	@if ! docker info 2>/dev/null | grep -q "Username"; then \
		echo "Not logged into Docker Hub. Please run: docker login"; \
		exit 1; \
	fi
	docker buildx build \
		--platform $(PLATFORMS) \
		--provenance=true \
		--sbom=true \
		--build-arg VERSION=$(VERSION) \
		-f Dockerfile \
		-t $(DOCKER_HUB_ORG)/$(IMAGE_NAME):$(VERSION) \
		-t $(DOCKER_HUB_ORG)/$(IMAGE_NAME):latest \
		--push \
		.

clean:
	docker rmi $(DOCKER_HUB_ORG)/$(IMAGE_NAME):$(VERSION) || true
	docker rmi $(DOCKER_HUB_ORG)/$(IMAGE_NAME):latest || true

inspect-attestations:
	@echo "SBOM:"
	@docker buildx imagetools inspect $(DOCKER_HUB_ORG)/$(IMAGE_NAME):$(VERSION) --format '{{ json .SBOM }}'
	@echo "\nProvenance:"
	@docker buildx imagetools inspect $(DOCKER_HUB_ORG)/$(IMAGE_NAME):$(VERSION) --format '{{ json .Provenance }}'

run-local:
	docker run -p 5000:5000 -e DATABASE_URL=postgresql://user:pass@host/db $(DOCKER_HUB_ORG)/$(IMAGE_NAME):$(VERSION)