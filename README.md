# Locust Server

Locust Server allows you to start multiple Locust tests each within its own Locust cluster with a single mouse click.

### Running

Locust Server can be run locally in which case it needs access to kube config 
in order to communicate with Kubernetes cluster:

```bash
docker run --rm -p 3001:8000 -v ${HOME}/.kube:/root/.kube -it inikolaev/locust-server
```

It can also be deployed to Kubernetes with provided descriptor:

```bash
kubectl apply -f locust-server.yaml
```

### Development

The project consists of two modules: `client` and `server`. `client` is a web-based user interface written in React, 
and `server` implements API used to create tests and start/stop Locust clusters written in Python and FastAPI.

#### Prerequisites

You would need the following software installed for development:

* Python 3
* Node JS
* `yarn`
* `kubectl`
* `helm`, tested with version 3 only, don't know whether it works with version 2


#### Install dependencies

For Python dependencies it's recommended to create a virtual environment to install them into first, which can be done with the following command:

```bash
# Create virtual environment
python3 -m venv /path/to/new/virtual/environment

# Activate virtual environment
source /path/to/new/virtual/environment/bin/activate
``` 

Now you can install dependencies with this command:

```bash
make init
```

#### Start server

```bash
make start-server
```

#### Start client

```bash
make start-client
```

### Screenshots

<img src="list.png">
<img src="create.png">
<img src="update.png">