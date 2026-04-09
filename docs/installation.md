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
sudo apt install -y openjdk-17-jre-headless
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
sudo mv nextflow /usr/local/bin/
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
apptainer version
```

### Extra WSL step
If you're on WSL, you will also need to install the nvidia-container-toolkit to utilise the GPU. Start by adding the libnvidia-container repository to the keyring:
```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
```

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
```

After the addition to the keyring the package can be installed:

```bash
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

### Verify installation with GPU
**Ubuntu**:
```bash
apptainer exec --nv docker://nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```
**WSL**:
```bash
apptainer exec --nvccli docker://nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```
If nvidia-smi shows the systems GPU details the Apptainer installation is working correctly with the systems GPUs. You can move on to [verify the setup](#3-verify-the-environment-with-gpu).

## 2.2 Docker
Check if Docker is already installed:
```bash
docker --version
```
If it is, you can skip to the Docker GPU section. If not, proceed below.

### Install Docker

Rootless Docker lets you run Docker [**without root privileges**](https://docs.docker.com/engine/security/rootless/), improving isolation and security.  

First install Docker dependencies:
```bash
sudo apt install -y uidmap dbus-user-session iptables
```
Then proceed with installing rootless Docker:
```bash
curl -fsSL https://get.docker.com/rootless | sh
```
Setup environment variables:
```bash
echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc
echo 'export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock' >> ~/.bashrc
source ~/.bashrc
````

Start the Docker services:
```bash
systemctl --user start docker
systemctl --user enable docker
```
Verify rootless Docker:
```bash
docker run hello-world
```

### Install libnvidia-container
[GPU access](https://docs.docker.com/compose/how-tos/gpu-support/) is needed for the de novo sequencers by installing the NVIDIA container toolkit. The commands below are typically enough for the installation, if not please refer to the [official guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

Add libnvidia-container to keyring:
```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
```

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
```

After the addition to the keyring, `nvidia-container-toolkit` can be installed:

```bash
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```
Restart the Docker services and update the config:
```bash
nvidia-ctk runtime configure --runtime=docker --config=$HOME/.config/docker/daemon.json
systemctl --user restart docker
sudo nvidia-ctk config --set nvidia-container-cli.no-cgroups --in-place
```
Now verify that Docker can access the GPU:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```
If nvidia-smi shows the systems GPU details the Docker installation is working correctly with the systems GPUs. You can move on to [verify the setup](#3-verify-the-environment-with-gpu).
## 3. Verify the environment with GPU

Before running NovoTax, make sure the foillowing commands work:

```bash
nextflow -version
```

## If using Docker
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## If using Apptainer

**Ubuntu**
```bash
apptainer exec --nv docker://nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**WSL**
```bash
apptainer exec --nv --nvccli docker://nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```


## Running NovoTax
If all of these work, you're now ready to run [NovoTax](example.md)!
