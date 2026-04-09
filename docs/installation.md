# Installation

NovoTax runs as a **Nextflow** pipeline and uses **Docker** containers for its software environment.

To run NovoTax locally, install:

- [**Java 17 or newer**](#1-install-java)
- [**Nextflow**](#2-install-nextflow)
- [**Docker**](#3-install-rootless-docker-with-gpu-support)

NovoTax is packaged as modular Docker files and designed to run through a workflow manager, so both Nextflow and Docker are part of the standard setup.

## Supported environment

NovoTax is intended to run on:

- **Windows through WSL2**
    - To install WSL, follow the guide on https://learn.microsoft.com/en-us/windows/wsl/install
- **Ubuntu**


macOS is not supported due to hardware limitations for the de novo sequencers.

## 0. System preparation

Ensure that all package channels are up-to-date

```bash
sudo apt update
```

## 1. Install Java

Nextflow requires Java.

Check whether Java is already available:

```bash
java -version
```

If needed, install **Java 17 or newer** using your system package manager or a JDK distribution of your choice. For example, using

```bash
sudo apt install openjdk-17-jre-headless
```

## 2. Install Nextflow

Check whether Nextflow is already available:

```bash
nextflow -version
```

If needed, install Nextflow with: # Note to 

```bash
curl -s https://get.nextflow.io | bash
```

This downloads the `nextflow` executable to the current directory.

Make it executable:

```bash
chmod +x nextflow
```

Move it somewhere in your `PATH`, for example:

```bash
sudo mv nextflow /usr/local/bin/
```

Confirm that Nextflow is installed:

```bash
nextflow -version
```

## 3. Container platform

NovoTax utilises containerisation for reproducability and modularity. There's two main container platforms supported, Apptainer and Docker. If Docker is already installed and working (`docker --version`) we recommend continuing using that. If this is the first time you use containers or work in an HPC environment we instead recommend Apptainer

## 3.1 Apptainer

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:apptainer/ppa
sudo apt update
sudo apt install -y apptainer
```

```bash
apptainer exec --nv docker://nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## 3.2 Docker

```bash
docker --version
```

If not Docker needs to be installed.

Rootless Docker lets you run Docker [**without root privileges**](https://docs.docker.com/engine/security/rootless/), improving isolation and security.  

[GPU access](https://docs.docker.com/compose/how-tos/gpu-support/) is needed for de novo sequencers by installing the [NVIDIA container toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). The installation differs depending on your chosen platform. Follow the instructions below for:
- [WSL](#31-wsl)
- [Ubuntu](#32-ubuntu)

## 3.1 WSL

### Install
```bash
sudo apt install -y uidmap dbus-user-session iptables
```
```bash
curl -fsSL https://get.docker.com/rootless | sh
```
---

### Setup Environment

```bash
echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc
```
```bash
echo 'export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock' >> ~/.bashrc
```
```bash
source ~/.bashrc
```

---

### Start Docker

```bash
systemctl --user start docker
```
```bash
systemctl --user enable docker
```

---

### Verify rootless Docker
```bash
docker run hello-world
```

---

### Setup NVIDIA container toolkit

Test that the GPU is available within WSL, try

```bash
nvidia-smi
```

If this fails, fix Windows NVIDIA driver issues. The issue is unlikely to lie within WSL.

If it works, you can setup the NVIDIA container toolkit, first by adding the NVIDIA channel to the keyring:

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
```

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
```

After these steps it is required to update the channel list:

```bash
sudo apt-get update
```

```bash
sudo apt-get install -y nvidia-container-toolkit
```

```bash
nvidia-ctk runtime configure --runtime=docker --config=$HOME/.config/docker/daemon.json
```

The previous step requires that docker is restarted:

```bash
systemctl --user restart docker
```
```bash
sudo nvidia-ctk config --set nvidia-container-cli.no-cgroups --in-place
```

Docker should now be able to access the GPU and CUDA toolkit. Running the command below should show GPU and driver details.

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

Before running NovoTax, [check that the environment is ready](#4-check-that-the-environment-is-ready).

## 3.2 Ubuntu

```bash
curl -fsSL https://get.docker.com/rootless | sh
```



Rootless Docker **can use GPUs**, but requires the NVIDIA Container Toolkit.

> Docs: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

Install toolkit:

```bash
sudo apt install -y nvidia-container-toolkit
```

Configure for rootless Docker:

```bash
nvidia-ctk runtime configure --runtime=docker --config=$HOME/.config/docker/daemon.json
```
```bash
systemctl --user restart docker
```

> Note: Rootless mode needs a user-level config and may require `no-cgroups = true` in NVIDIA config.

Running the command below should show GPU and driver details.

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

Before running NovoTax, [check that the environment is ready](#4-check-that-the-environment-is-ready).

---

## 4. Check that the environment is ready

Before running NovoTax, make sure these commands work:

```bash
java -version
```
```bash
nextflow -version
```
```bash
docker --version
```
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

If all of these work, the system is ready to run [NovoTax](example.md).