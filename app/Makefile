
KIND_CLUSTER ?= kind
K3D_CLUSTER ?= k3s-default

.PHONY: build
build:
	docker build -t badapp:latest .


.PHONY: load
load: build
	kind load docker-image --name $(KIND_CLUSTER) badapp:latest || k3d image import badapp:latest --cluster $(K3D_CLUSTER) --mode direct
