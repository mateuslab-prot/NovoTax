# Installation

NovoTax runs as a **Nextflow** pipeline and uses modular **containers** for its software environment.

To run NovoTax locally, the following tools are needed:

- [**Nextflow**](https://www.nextflow.io)
- [**Docker**](https://www.docker.com) or [**Apptainer**](https://apptainer.org)

## Supported environment

NovoTax is intended to run on:

- **Windows through WSL2**
    - To install WSL, follow the guide [official guide](https://learn.microsoft.com/en-us/windows/wsl/install)
- **Ubuntu**


macOS is not supported due to hardware limitations for the de novo sequencers.

## 0. System preparation

Ensure that all package channels are up-to-date

```bash
sudo apt update
```

## 1.  Install Nextflow

Check whether Nextflow is already available:

```bash
nextflow -version
```

If not, the steps below is enough for a typical installation. If you face problems during this, please refer to the [official documentation](https://docs.seqera.io/nextflow/install).

### Install Java
Nextflow requires Java 17 (or later, up to 26). Check which version of Java you have with:
```bash
java -version
```

If you don't have a compatible version of Java installed, it is recommended that you install it through SDKMAN.

1. If needed, install Java 17 or newer using your system package manager or a JDK distribution of your choice. For example, using
```bash
sudo apt install openjdk-17-jre-headless
```
2. Confirm Java is installed correctly:
```bash
java -version
```

### Install Nextflow
1. Download Nextflow:
```bash
curl -s https://get.nextflow.io | bash
```
2. Make Nextflow executable:
```bash
chmod +x nextflow
```

3. Move Nextflow into an executable path. For example:
```bash
mkdir -p $HOME/.local/bin/
mv nextflow $HOME/.local/bin/
```

### Verify installation
Verify that Nextflow is installed correctly:
```bash
nextflow -version
```

## 2. Container platform

NovoTax utilises containerisation for reproducability and modularity. There's two main container platforms supported, Apptainer and Docker. If Docker is already installed and working (`docker --version`) we recommend continuing using that. If this is the first time you use containers or work in an HPC environment we instead recommend Apptainer due to easier installation and usage.

## 2.1 Apptainer

Check if Apptainer is already available:
```bash
apptainer version
```

If not, the steps below is enough for a typical installation. If you face problems during this, please refer to the [official guide](https://apptainer.org/docs/admin/main/installation.html).

### Install Apptainer
```bash
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:apptainer/ppa
sudo apt update
sudo apt install -y apptainer
```

### Verify installation
```bash
apptainer exec --nv docker://nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## 2.2 Docker

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

Before running NovoTax, make sure the foillowing commands work:

```bash
nextflow -version
```

## If using Docker
```bash
docker --version
```
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## If using Apptainer

### Ubuntu
```bash
apptainer exec --nv docker://nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### WSL
```bash
apptainer exec --nv --nvccli docker://nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```


## Running NovoTax
If all of these work, you're now ready to run [NovoTax](example.md)!
