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
Draft for py-spy

(cd app && make load)

kubectl run bad-app --image=badapp:latest --image-pull-policy=Never --restart=Never

make load
kubectl debug -it bad-app --image=debug-tools --image-pull-policy=Never --target=bad-app

    py-spy dump --pid 1
    py-spy top --pid 1
    py-spy record --pid 1 -o flame.svg --duration 10

kubectl cp bad-app:/flame.svg -c debugger-jh9fj $PWD/flame.svg
                                 ^------------^

  k get po bad-app -ojson | jq -r '.spec.ephemeralContainers[-1].name'

-->
