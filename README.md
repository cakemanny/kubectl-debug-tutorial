<!--

The aim here should be to go a little bit further than
https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/#ephemeral-container

i.e. have working examples for a python application,
maybe using
- py-spy
- memray

a more general solution using bpftrace ?

-->
# Holistic Debugging in Production with `kubectl debug`

## Forces
- You run ultra-slim production images to reduce their attack surface area.
  That means no shell programs, debuggers nor privileges.

- You have a performance problem you are unable to understand using logs and
  distributed tracing.

## Approach

Create a second docker image loaded with your debuggers and other tools.
Use [`kubectl debug`](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_debug/)
to inject a tools container into the pod to examine the application.


https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/#ephemeral-container

## Forces
- Your application is running in production. Attaching a debugger would
  interrupt real user requests.

## Approach
Use holistic non-intrusive debugging techniques
- py-spy
- bpftrace

<!--
## Draft for py-spy

make -C app load

kubectl run bad-app --image=badapp:latest --image-pull-policy=Never --restart=Never
kubectl port-forward pod/bad-app 8000:8000 &  # or in another terminal

make load
kubectl debug -it bad-app --image=debug-tools --image-pull-policy=Never --profile=general --target=bad-app
                  ^-----^                                                                          ^-----^
#                target pod                                                                     target continer

    py-spy dump --pid 1
    py-spy top --pid 1
    py-spy record --pid 1 -o flame.svg --duration 10

kubectl cp bad-app:/flame.svg -c debugger-jh9fj $PWD/flame.svg
                                 ^------------^

  k get po bad-app -ojson | jq -r '.spec.ephemeralContainers[-1].name'


kubectl debug -it backend-689b8cc9-9572s --image=debug-tools --image-pull-policy=Never --profile=general --target=uwsgi

-->

<!--

## Run badapp with a memory limit

kubectl run bad-app --image=badapp:latest --image-pull-policy=Never --restart=Never \
  --overrides='{
    "spec": {
        "containers": [
            {
                "name": "bad-app",
                "image": "badapp:latest",
                "resources": {
                    "requests": {
                        "memory": "128Mi"
                    },
                    "limits": {
                        "memory": "128Mi"
                    }
                },
                "imagePullPolicy": "Never"
            }
        ]
    }
}'

TODO: I think the cluster nodes need to have a memory limit for this to
end up being effectful.
https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#my-container-is-terminated
> If a container exceeds its memory request and the node that it runs on becomes short of memory overall, it is likely that the Pod the container belongs to will be evicted.

-->

Further Reading:

- https://github.com/aylei/kubectl-debug/blob/master/docs/examples.md
- https://www.cncf.io/blog/2022/03/25/koolkits-kubernetes-debugging-reimageined/
