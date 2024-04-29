
KIND_CLUSTER ?= kind
K3D_CLUSTER ?= k3s-default

.PHONY: build
build:
	docker build -f tools.dockerfile -t debug-tools .

.PHONY: load
load: build
	kind load docker-image --name $(KIND_CLUSTER) debug-tools || k3d image load debug-tools --cluster $(K3D_CLUSTER) --mode direct
