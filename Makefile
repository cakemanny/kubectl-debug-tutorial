
.PHONY: build
build:
	docker build -f tools.dockerfile -t debug-tools .

.PHONY: load
load: build
	kind load docker-image debug-tools || k3d image load debug-tools
