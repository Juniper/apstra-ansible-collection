![Juniper Networks](https://juniper-prod.scene7.com/is/image/junipernetworks/juniper_black-rgb-header?wid=320&dpr=off)

# EDA Decision Environment (DE) Container

This folder contains procedure to build container image for running Ansible automation using the `ansible-rulebook` tool in a containerized fashion, and use it in the EDA Automation Controller. The image is designed to facilitate Event Driven Automation (EDA) with Ansible, providing the necessary components and dependencies to execute Ansible rulebooks seamlessly.

## Container Image

The container image is based on the `registry.access.redhat.com/ubi9-minimal` base image and includes the following components:

- Java 17
- Python 3.11
- GCC (GNU Compiler Collection)
- Ansible
- Ansible Collections:
  - ansible.eda
  - dynatrace.event_driven_ansible
  - kubealex.eda
  - kubealex.general
  - redhatinsights.eda
  - junipernetworks.eda

- Other Python packages necessary for event-driven automation:
  - asyncio
  - aiokafka
  - aiohttp
  - aiosignal
  - asyncio_mqtt
  - kubernetes
  - psycopg_binary
  - requests


## Pre requisites

1. **Installing ansible builder**:

   Installing ansible builder using PIP

   ``` bash
   pip3 install ansible-builder
   ```
   There are other alternatives methods of installing ansible builder can be followed from the [here](https://ansible.readthedocs.io/projects/builder/en/latest/installation/)


## Instructions

Follow the steps below to use the container image for event-driven automation with Ansible.

### Method-1

1. **Build the container image**:

   To build the container image locally, execute the following command in the directory containing the provided `ansible builder file`:

   ```bash
   ansible-builder build -t apstra-eda-de -f de-builder.yml
   ```

2. **Push the container image**

   To push the container image in a remote repository log-in, tag and push the image:

   ```bash
   docker login
   docker tag apstra-eda-de:latest <REGISTRY_URL>/apstra-eda-de:<TAG>
   docker push <REGISTRY_URL>/apstra-eda-de:<TAG>
   ```
### Method-2

Alternatively you can run the script build_image.sh which will ask for REGISTRY_URL and TAG as input and build, tag and push the image.

Below example will build the image and push it to s-artifactory.juniper.net/atom-docker/eda and tag it as v1.

  ```bash
  ./build_image.sh s-artifactory.juniper.net/atom-docker/eda v1
  ```

By default,this script build_image.sh  will push the image to s-artifactory.juniper.net/atom-docker/eda when you do not mention the REGISTRY_URL.

  ```bash
  ./build_image.sh v1
  ```
Above will tag build, tag and push the image as s-artifactory.juniper.net/atom-docker/eda/apstra-eda-de:v1.

You are now ready to use it as a standalone container or in EDA Controller.
