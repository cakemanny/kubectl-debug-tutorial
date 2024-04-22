
.PHONY: build
build:
	docker build -t badapp:latest .


.PHONY: load
load: build
	kind load docker-image badapp:latest || k3d image load badapp:latest
