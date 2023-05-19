# EnergyPlus MutiLaunch
  
__Version__: 0.41 BETA  
__Updated__: 2023-05-19

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

### Settings & Initial Configuration

![Advanced Settings](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_advanced_settings.png)

Under the `Advanced Settings` tab, set the following.

1. Series or Parallel
  1. Series: Runs simulations one at a time, waiting for the previous one to complete before starting the next one. This is similar to the EP Launch "Group of Input Files" feature and is recommended for basic EnergyPlus simulations.
  2. Parallel: Starts a new simulation at a regular time interval dictated by "Wait time between launches in seconds" regardless of whether the previous simulations have completed. This is useful for co-simulation with GridLab, Python, UCEF, or other similar frameworks if multiple interactive models must be simulated.
2. Wait time between launches in seconds: For parallel only, how many seconds to wait before starting the next model. This prevents CPU overload or other crashing issues because for most EnergyPlus models, there is an initial warmup period which is very computationally intense. This allows time for the previous warmup to complete before starting the next one. The default is 30 seconds.
3. EnergyPlus installation directory: The full folder path to where EnergyPlus is installed on this computer. 

Click `Apply` to save settings.

### Setting Up Simulations

There are three methods for selecting which EnergyPlus model files and weather files to run.

#### 1. Select Files to Run

This mode allows you to manually select the .idf files and the .epw file to use. Files can be in different directories.

![Select files to run](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_select_1.png)

Click `Select .idf files`

Select one or more files you want to run.

![browse idf](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_select_browse_IDF.png)

The selected .idf files will appear in the box below. If you need to add more files, click `Select .idf files` and browse for any additional files. If you need to remove files from the list, click on any that you no longer want so they are highlighted, then click  `Remove selected files`.

![remove idf](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_remove_idf.png)
![remove idf 2](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_remove-after.png)

`Select .epw file` and browse for the weather file. This weather file will be used for all above simulations.

![browse epw](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_select_browse_weather.png)

The status bar will turn bright blue and say "Simulations Ready".

![Simulations ready](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_select_ready.png)

Proceed to "Running Simulations"

#### 2. Autodetect 

This mode is a shortcut to automatically find all .idf files and the .epw file in a single directory and recursively into its subdirectories. There must be exactly one .epw file in the directory that will be used for all .idf files. Currently, there is no way to exclude individual files or add a second root directory, so this requires all simulation files to be organized in one folder.

![Autodetect start](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_autodetect_1.png)

Click `Browse Folder` and select a folder using the dialog.

If it successfully found the files, it will show a list of .idf files detected and the .epw file. The status bar will turn bright blue and say "Simulations Ready"

![Autodetect ready](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_autodetect_ready.png)

Proceed to "Running Simulations"

#### 3. Queue File

This is an advanced method for running repeated batches of simulations that may be spread across many directories. Individual simulations can use different .epw files. The queue file must be a .csv with the following columns:

Filename: The name of the .idf file.  
Filepath: Full file path to the .idf file.  
Weather: Full file path to the .epw file used for this .idf file

Example:

|Filename|Filepath|Weather|
|---|---|---|
|building1.idf|Z:/EnergyPlus/building_files/building1.idf|Z:/EnergyPlus/weather_files/weather1.idf|
|building2.idf|Z:/EnergyPlus/building_files/building2.idf|Z:/EnergyPlus/weather_files/weather2.idf|
|building3.idf|Z:/different/directories/building3.idf|Z:/EnergyPlus/weather_files/weather1.idf|

In the above example, building1 will be run with weather1, building2 with weather2, and building3 with weather1.

![queue start](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_queue_1.png)

### Running Simulations

When you have successfully selected the .idf and .epw files to run, the status bar in the bottom should turn bright blue and say "Simulations Ready." This demo is using the Select Files to Run method, but is the same for all three.

![Simulations ready](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_select_ready.png)

Click `Run Simulations`. The status bar will turn yellow and display a message that simulations are running. The window may freeze or say "Not Responding" - this is normal behavior and indicates the simulations are running. It may remain unresponsive until all simulations are complete, which can be hours or more depending on your simulations. Do not close the window or kill the program. 

![simulations running](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_select_running.png)

When complete, it will display the green success message.

![success](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_status_simulations_completed_successfully.png)

### Error Messages

One or more of the selected .idf files is corrupt or cannot run.
![error invalid idf](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_status_error_invalid_idf.png)

Queue file is the wrong file type, is formatted incorrectly, or does not exist.
![error invalid queue](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_status_error_invalid_queue.png)

Folder and subdirectories do not contain any valid .idf files.
![error no idf found](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_status_error_no_idf_found_folder.png)

Folder and subdirectories do not contain any valid .epw files.
![error no epw found](https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch/blob/main/epml_screenshots/epml_status_error_no_epw_found_folder.png)

For debugging, look at the _epml\_out.log_ file to check for additional error messages.

## Known Issues

1. Slab and Basement calculations do not work when running EnergyPlus via command line. These must still be run in EP Launch. 
2. GUI controls for removing .idf files under the Select .idf files box are extremely buggy. 
  1. It can be difficult to tell which are selected
  2. Sometimes if you remove a file, it will think there are no files left and request to add more .idfs before running
  3. Removing .idfs can cause it to return an invalid filepath error.

## Contributors & Acknowledgements
Santa Clara University, School of Engineering, Department of Mechanical Engineering, Smart Grid & Residential Energy Simulation Team. Portions of the development and research are made possible through the support of NIST via federal awards #70NANB20H204 and #70NANB22H159, and by internal support by the School of Engineering at Santa Clara University

__Author__: [Brian Woo-Shem](https://www.brianwooshem.com)

Licensed under the GNU General Public License v3

EnergyPlus is a trademark of the US Department of Energy. EnergyPlus MultiLaunch is an independent project and is not affiliated nor endorsed by the US Department of Energy.
