# Software Setup for the Image-Bot

[Go back to main page](../README.md)

> We are currently working on an installation procedure which does not rely on git. However, until now we require you explicitly to use git.
> If you are not familiar with git, please look for a tutorial (e.g. [here](https://www.computerhope.com/issues/ch001927.htm) for windows or [here](https://www.linux.com/topic/desktop/introduction-using-git/) for linux).  
>  
> In this file, different terminal "types" are referenced: git, env and global. They refer to their scope in the project.  
> On Linux, the default bash terminal can be used for any type.  
> On Windows, it is possible to choose between Git Bash (recommended) and Powershell.

## 0. Install python and git (if not already present)

For the Image-Bot to work, you will need python and git.

Please download and install python and git (e.g. from the links below):

* Python:  
  Windows: [https://www.python.org/downloads/](https://www.python.org/downloads/)  
  Linux: Use your package-manager to install python (eg. ```sudo apt install python``` on Ubuntu)

  Select a version to install. Python 3.8 is recommended, but newer versions should be compatible.

* Git:  
  Windows: [https://git-scm.com/download/win](https://git-scm.com/download/win)  
  Git for Linux is most likely

## 1. Clone the repository and initialize submodules

Go to the folder where you want to install the Image-Bot. Open your (git) terminal and type:

```(bash)
git clone https://github.com/MobilityInnovation/Image-Bot
```

Enter the newly created folder, which contains the Image-Bot's software pipeline:

```(bash)
cd Image-Bot
```

Initiliaze and clone the submodules:

```(bash)
git submodule init
git submodule update
```

Close your (git) terminal. We are done with git.

## 2. Install and activate virtual environment

Open your (env) terminal in the new "image-bot" folder and create a virtual environment:

```(bash)
python -m venv .venv
```

This creates a new folder called .venv containing the virtual environment.  
Activate the virtual environment:

```(bash)
# Windows Powershell
./.venv/Scripts/activate.ps1

# Windows Git Bash
source ./.venv/Scripts/activate

# Linux, Git Bash
source ./.venv/bin/activate

# Deactivate virtual environment
deactivate
```

Open your (env) terminal in the new "Image-Bot" folder and install the required dependencies:

```(bash)
python -m pip install -r requirements.txt
```

The ImageBot is now ready to use with conventional python files (placed in this repos root). To enable Jupyter support, follow these steps:

1. Using (global or env) terminal, install jupyter

    ```(bash)
    python -m pip install jupyterlab
    ```

2. Using (env) terminal, install the ipykernel and register it

    ```(bash)
    ipython kernel install --user --name=image-bot-kernel
    ```

Close your (env) terminal. We are done with it.

## 3. Fill the background images folder

Background images are the images, in which the masked objects will be blended. The Image-Bot does not come with background images. As such enter the folder "bgs" and copy a set of divers background images in there.
You can for example use a random subset from the [COCO Dataset](https://cocodataset.org/). We suggest to have around 5,000 different background images.

## 4. Use the Image-Bot

Please have a look at the [User Manual](UserManual.md).
