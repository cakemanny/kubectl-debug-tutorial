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

### Forces
- You run ultra-slim production images to reduce their attack surface area.
  That means no shell programs, debuggers nor privileges.

- You have a performance problem you are unable to understand using logs and
  distributed tracing.

### Approach

Create a second docker image loaded with your debuggers and other tools.
Use [`kubectl debug`](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_debug/)
to inject a tools container into the pod to examine the application.


https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/#ephemeral-container

### Forces
- Your application is running in production. Attaching a debugger would
  interrupt real user requests.

### Approach
Use holistic non-intrusive debugging tools
- [py-spy](https://github.com/benfred/py-spy)
- [bpftrace](https://bpftrace.org/)
- [async-profiler](https://github.com/async-profiler/async-profiler)


## Tutorial

### Prerequisites

You need to have a local kubernetes cluster running and your kubectl context
directed at it.

If you have no preference, try
[kind](https://kind.sigs.k8s.io/docs/user/quick-start/) but [k3d](https://k3d.io/)
should also work.

[Docker](https://docs.docker.com/engine/install/) is used to build images.
(It should be possible to use [nerdctl](https://github.com/containerd/nerdctl)
or [podman](https://podman.io/) with a docker alias but is not tested.)

[jq](https://jqlang.github.io/jq/) is not required but might come in handy.

### Components

**bad-app**

Bad app is a simple python http server that does a little bit of work.
See [app/src/badapp/cli/serve.py](app/src/badapp/cli/serve.py).

We've used a [distroless](https://github.com/GoogleContainerTools/distroless)
image as a base so that we have no superfluous overhead; only what is needed
to run our python app. See [app/Dockerfile](app/Dockerfile).

### Using [`py-spy`](https://github.com/benfred/py-spy)

**Load bad-app**

```sh
## Build the bad-app app and load it into our cluster
make -C app load
# docker build -t badapp:latest .
# ...
# Image: "badapp:latest" with ID "sha256:26b664207b7481053678b203f4ce65b21fd264c91f2c7c4ba3d1b065668592f8" not yet present on node "kind-control-plane", loading...

kubectl run bad-app --image=badapp:latest --image-pull-policy=Never --restart=Never
# pod/bad-app created

## Let's add a port forward so we can test  /-- alt: run in a 2nd terminal
kubectl port-forward pod/bad-app 8000:8000 &
# Forwarding from 127.0.0.1:8000 -> 8000
# [1] 99198

curl http://localhost:8000/
# is this what you are looking for?: $2b$12$xmUh1CzAXRSqxc8KYhmaRu6gtEgusi03NVt/fdGxLuLi6hGK60jQK
```

> [!NOTE]
> If you are not using the default cluster name you may need to set the
> `KIND_CLUSTER` or `K3D_CLUSTER` env vars.

🤔🌧 ... hmmm .... feels a bit slow.

Let's debug!

If we try to exec into our pod, we see there's no shell
```sh
kubectl exec bad-app -- sh
# error: Internal error occurred: error executing command in container: failed to exec in container: failed to start exec "20c9b014f639deebb89b37fb911f1b059abcfe25a20430f44d4906b32a390b99": OCI runtime exec failed: exec failed: unable to start container process: exec: "sh": executable file not found in $PATH: unknown
```

But what about that `kubectl debug` that someone wrote about further up the page?

Luckily we've built a tools image that has everything we need to debug our
app. See [tools.dockerfile](tools.dockerfile). ... Ok... maybe just `py-spy`.

```sh
## Let's load our tools into the cluster
make load
# ...
# Image: "debug-tools" with ID "sha256:25a6f3dda4e17089761b80890dc7b311a236a5e52199efa804c7370c83a7f0e7" not yet present on node "kind-control-plane", loading...

##                                         we only do this because we loaded
##                                       debug-tools directly into the cluster
##                                            v-----------------------v
kubectl debug -it bad-app --image=debug-tools --image-pull-policy=Never --profile=general --target=bad-app
##                ^-----^                                                                          ^-----^
##               target pod                                                                     target continer
##
##                             we might use this shortly
##                                   v------------v
# Defaulting debug container name to debugger-sk9nf.
# root@bad-app:/#
```

Now we can debug! By default our debug pod shares a process namespace with
the target container. This means pid 1 is the pid 1 of our target container
i.e. the first process we started i.e. our app.

```sh
## Inside our debug container:
py-spy dump --pid 1
# Process 1: /usr/bin/python3.11 /app/badapp.pyz
# Python v3.11.2 (/usr/bin/python3.11)
#
# Thread 1 (idle): "MainThread"
#     select (selectors.py:415)
#     serve_forever (socketserver.py:233)
#     main (serve.py:41)
#     run (__init__.py:38)
#     bootstrap (__init__.py:253)
#     <module> (__main__.py:3)
#     _run_code (<frozen runpy>:88)
#     _run_module_as_main (<frozen runpy>:198)
```

We can see over the course of time, where time is spent in our app.
```sh
py-spy top --pid 1
## Run your `curl localhost:8000` command in another terminal to see something interesting here.
```

And for our final trick, let's produce a flamegraph
```sh
py-spy record --pid 1 -o flame.svg --duration 10
```

While that's running, it might be useful to generate some load:
```sh
## In a local 2nd terminal
bash -c 'for i in {1..20}; do curl http://localhost:8000/; done'
```

Now let's grab that flame and copy it to local machine:
```sh
## In our local 2nd terminal:
## We need that debug container name from earlier. In case we lost it, don't
## worry, we can find it out again:
kubectl get po bad-app -ojson | jq -r '.spec.ephemeralContainers[-1].name'
# debugger-sk9nf

kubectl cp bad-app:/flame.svg -c debugger-sk9nf $PWD/flame.svg
##                               ^------------^
##                              stick that here
# tar: Removing leading `/' from member names
## we can ignore this message from tar
```

Now we can dig into our flamegraph. Let's open it with a web browser
```sh
## e.g. macOS
open -a 'Google Chrome' flame.svg
## some possibilities on Linux
google-chrome flame.svg
chromium flame.svg
```

**Some final observations:**

```sh
## locally:
kubectl get po bad-app -ojson | jq -r '.spec.ephemeralContainers[-1]'
# {
#   "image": "debug-tools",
#   "imagePullPolicy": "Never",
#   "name": "debugger-gn6k4",
#   "resources": {},
#   "securityContext": {
#     "capabilities": {
#       "add": [
#         "SYS_PTRACE"
#       ]
#     }
#   },
#   "stdin": true,
#   "targetContainerName": "bad-app",
#   "terminationMessagePath": "/dev/termination-log",
#   "terminationMessagePolicy": "File",
#   "tty": true
# }
```

Choosing the `--profile=general` has given us the `SYS_PTRACE` capability,
that's what's allowed `py-spy` to attach to our python process.


```sh
kubectl logs bad-app -c debugger-gn6k4
## we end up seeing a reproduction of our debugging session.
```

> [!WARNING]
> The ephemeral container session is emitted to the kubernetes logging system.
> Any sensitive data you inspect may be sent to your production log analysis
> system.


### Key Observations

- We didn't need to restart our pod or change our code in order to debug our app.

### Cleaning up

```sh
kubectl delete pod bad-app
# pod "bad-app" deleted
```

At this point, feel free to delete the local cluster if you created it just
for the tutorial.

We can also delete those docker images we created.
```sh
docker image rm debug-tools:latest badapp:latest
```

## Further Reading

- The KEP for `kubectl debug` includes
  https://github.com/kubernetes/enhancements/blob/master/keps/sig-cli/1441-kubectl-debug/README.md
- https://www.cncf.io/blog/2022/03/25/koolkits-kubernetes-debugging-reimageined/
