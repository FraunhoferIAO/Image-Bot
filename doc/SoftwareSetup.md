# Software Setup for the Image-Bot

[Go back to main page ](../README.md)

Please note: We are currently working on an installation procedure which does not rely on git nor conda. However, until now we require you explicitly to use git and conda.
If you are not familiar with git, please look for a tutorial (e.g. [here](https://www.computerhope.com/issues/ch001927.htm) for windows or [here](https://www.linux.com/topic/desktop/introduction-using-git/) for linux).
If you are not familiar with conda, feel free to look for a tutorial. However, the steps with conda are also explained in detail in the following. Thus, deep knowledge of conda ist not necessary.

## 0. Install git and conda (if not already present)

For the Image-Bot to work, you will need git and conda.

Please download and install git and conda (e.g. from the links below):

* Anaconda: https://docs.anaconda.com/anaconda/install/
* Git for windows: https://git-scm.com/download/win
* Git for linux is most likely delivered with your distribution

Please note that the Image-Bot is mainly build in python. As such, you will also need a python environment. Python is normally installed with and managed by Anaconda. As such, no further steps are required.

## 1. Clone the repository and initiliaze the submodules

Go to the folder where you want to install the Image-Bot. Open your (git) terminal and type:

```
git clone https://github.com/MobilityInnovation/Image-Bot
```

Enter the newly created folder, which contains the Image-Bot's software pipeline:

```
cd image-bot
```

Initiliaze and clone the submodules:

```
git submodule init
git submodule update
```

Close your (git) terminal. We are done with git.

## 2. Install and activate conda environment

Open your (anaconda) terminal in the new "image-bot" folder and install the required conda environment from the supplied file:

```
conda env create -f environment.yaml
```

To use the environment, activate it with the command

```
conda activate image-bot
ipython kernel install --user --name=image-bot-kernel
conda deactivate
```

Close your (anaconda) terminal. We are done with anaconda.

## 3. Fill the background images folder

Background images are the images, in which the masked objects will be blended. The Image-Bot does not come with background images. As such enter the folder "bgs" and copy a set of divers background images in there.
You can for example use a random subset from the [COCO Dataset](https://cocodataset.org/). We suggest to have around 5,000 different background images.

## 4. Use the Image-Bot

Please have a look at the [User Manual](UserManual.md).