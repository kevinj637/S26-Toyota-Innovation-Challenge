# Setting up this environment

## You will need: Python, Arduino IDE install on your computer

## Install the following VSCode extensions(at a minimum):
 - Jupyter
 - Python
 - Python Environments

## Run the following commands to setup the rest of the script

### Windows

Run the following commands in the terminal:
```
python3 -m venv ./venv
.\venv\scripts\activate.ps1
pip install -r requirements.txt

```

Then download the Toyota Data files from here (HUGE FILE WARNING):
**Please only download the robot 07 files. No need to download the entire dataset (we won't have time anyways for the whole dataset)**

[Google Drive](https://drive.google.com/drive/folders/1WH95WIw2kX9aDbsBe2MpxEcpnStesaIB?usp=sharing)
https://drive.google.com/drive/folders/1WH95WIw2kX9aDbsBe2MpxEcpnStesaIB?usp=sharing

Extract and put the files into a folder called ```data```. 
Move the downloaded files into folder ```data``` (case-sensitive) and uncompress the files.
**Note: You may need to install 7zip or WinZip to unzip the files properly**

### Manually extracting and moving files into folder ```data``` is the simplest way for inexperienced users. 

If you want the following code may accomplish the same:
```
mkdir data
unzip .\__compressed_download_file__.zip
move -Path ".\robot_7*" -Destination ".\data"
del -Path ".\__compressed_download_file__.zip"
cd data
unxz *
cd ..
```

### Mac/Linux

Run the following commands in the terminal:
```
python3 -m venv ./venv
source venv/bin/activate
pip install -r requirements.txt

```
Then: download the Toyota Data file from here (HUGE FILE WARNING):
[Google Drive](https://drive.google.com/drive/folders/1WH95WIw2kX9aDbsBe2MpxEcpnStesaIB?usp=sharing)
https://drive.google.com/drive/folders/1WH95WIw2kX9aDbsBe2MpxEcpnStesaIB?usp=sharing

Move the file into this folder

Then download the Toyota Data files from here (HUGE FILE WARNING):
**Please only download the robot 07 files. No need to download the entire dataset (we won't have time anyways for the whole dataset)**

[Google Drive](https://drive.google.com/drive/folders/1WH95WIw2kX9aDbsBe2MpxEcpnStesaIB?usp=sharing)
https://drive.google.com/drive/folders/1WH95WIw2kX9aDbsBe2MpxEcpnStesaIB?usp=sharing

Extract and put the files into a folder called ```data```. 
Move the downloaded files into folder ```data``` (case-sensitive) and uncompress the files.
**Note: You may need to install 7zip or WinZip to unzip the files properly**

### Manually extracting and moving files into folder ```data``` is the simplest way for inexperienced users. 

If you want the following code may accomplish the same:
```
mkdir data
unzip __compressed_download_file__.zip
mv robot_7* data
rm __compressed_download_file__.zip
cd data
unxz *
cd ..
```

## Setup is now complete! You should now be able to run any listed programs!