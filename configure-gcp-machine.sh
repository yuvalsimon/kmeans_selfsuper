#!/bin/bash
## Machine: Google Cloud - Ubuntu 20.04 LTS - SSD 200GB 20 vCPU 130GB RAM 1 NVIDIA Tesla P4
sudo apt-get update
sudo apt-get -y install wget git linux-headers-$(uname -r) dkms build-essential pciutils tmux
sudo apt-get -y upgrade

# CUDA Toolkit 11.0
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/11.0.3/local_installers/cuda-repo-ubuntu2004-11-0-local_11.0.3-450.51.06-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2004-11-0-local_11.0.3-450.51.06-1_amd64.deb
sudo apt-key add /var/cuda-repo-ubuntu2004-11-0-local/7fa2af80.pub
sudo apt-get update
sudo apt-get -y install cuda

echo 'export PATH=/usr/local/cuda-11.0/bin${PATH:+:${PATH}}' >> ~/.profile
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.0/lib64\${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}' >> ~/.profile

sudo systemctl enable nvidia-persistenced
sudo systemctl start nvidia-persistenced

# Conda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O conda.sh
chmod +x conda.sh
./conda.sh -b
rm conda.sh
miniconda3/bin/conda init bash
sleep 1
source ~/.bashrc

# Project
git clone --recurse-submodules https://github.com/yuvalsimon/kmeans_selfsuper.git
pushd kmeans_selfsuper >> /dev/null
conda install pip
pip install -r requirements.txt
mkdir checkpoints
wget https://www.dropbox.com/sh/87d24jqsl6ra7t2/AAAzMTynP3Qc8mIE4XWkgILUa/InfoMin_800.pth?dl=1 -O checkpoints/InfoMin_800.pth
