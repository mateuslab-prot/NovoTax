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
If you're on WSL, you will also need to install the nvidia-container-toolkit to utilise the GPU:
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

After the addition to the keyring the package can be installed:

```bash
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

### Verify installation
**Ubuntu**:
```bash
apptainer exec --nv docker://nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```
**WSL**:
```bash
apptainer exec --nvccli docker://nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
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

## 2.3 nvidia-container-toolkit
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

After the addition to the keyring the package can be installed:

```bash
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

## 3. Check that the environment is ready

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
