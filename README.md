# EnergyPlus MutiLaunch
  
__Version__: 0.41 BETA  
__Updated__: 2023-05-18

Simple GUI to rapidly launch EnergyPlus simulations in parallel or series. A specialized alternative to EP Launch for researchers who need to run large quantities of EnergyPlus simulations. Especially well-suited for co-simulation applications where mutliple EnergyPlus models must run in parallel.

## Features

- Running bulk batches of simulations in parallel (launches multiple processes at once, useful for co-simulation)
    - Optional delay time to allow for warmup to complete
- Running bulk batches of simulations in series
- Detecting and running all simulations in a single folder and subfolders.
- Running simulations according to a saved queue file - useful when running a large batch of simulations repeatedly.

## Running in Python

### Prerequisites
- Python 3.7 or newer
- tkinter
- webbrowser
- time
- configparser
- subprocess
- os
- csv
- sys

### Instructions
1. Download the files and copy them to a single folder
2. Run _epml.py_

__Windows__:  

    Py epml.py

__Linux___:  

    python3 epml.py


## Running via executable (Windows only)

This feature is currently in development, please check back soon!

## Usage

Documentation in progress.

## Known Issues

1. Slab and Basement calculations do not work when running EnergyPlus via command line. These must still be run in EP Launch. 

## Contributors & Acknowledgements
Santa Clara University, School of Engineering, Department of Mechanical Engineering, Smart Grid & Residential Energy Simulation Team. Portions of the development and research are made possible through the support of NIST via federal awards #70NANB20H204 and #70NANB22H159, and by internal support by the School of Engineering at Santa Clara University

__Author__: [Brian Woo-Shem](https://www.brianwooshem.com)

Licensed under the GNU General Public License v3

EnergyPlus is a trademark of the US Department of Energy. EnergyPlus MultiLaunch is an independent project and is not affiliated nor endorsed by the US Department of Energy.
