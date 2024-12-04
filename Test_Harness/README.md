# Introduction
This directory contains the test harness component of MOAT. It allows for automated execution time testing using a variety of stressors and victim programs.

## Dependencies
* Linux host machine (not strictly necessary, but the framework was built under that assumption)
* Python 3.10 or higher
* Python `yaml` library
* Python `pyserial` library
* Python `matplotlib` library

## Preparation
There is one preparation step that must be performed before the user can use the test framework. This directory contains `launch_base.sh` which is used by the framework. This file manages execution of the victim program in Dom0 and must be copied to `/run/media/root-mmcblk0p2/` on the PetaLinux SD card.

## Framework Usage
The test framework is provided in the form of a Python file. The device that the user is hosting the test framework on should be a separate device from the test board and should be running Linux and a version of Python >= 3.10. The user should first proceed by attaching the serial connection from the test board to their host device. The framework assumes that the serial connection from the host device to the test board is enumerated as ttyUSB0 on the host system. The user should verify this before proceeding and change the device name in the main() function if necessary. 
When the user first runs the framework, they are presented with three choices: Terminal mode, MOATerm mode, and batch mode. Each of these options has a specific purpose. Terminal mode serves as a pure serial console and allows the user to directly issue commands and read responses from DomO. This mode is useful when debugging issues on the board. MOATerm mode is the first of two test modes that the framework supports. MOATerm allows the user to manually specify test parameters over one test run only. The user may specify the following test parameters:
* Friendly Test Name (used for results directory naming)
* Number of CPU cores to run interference generation on
* Type of interference to be run on a given CPU core
* Victim program that will be analyzed for execution time metrics (must be in the form of a valid stress-ng command, do not include --metrics or --yaml flags, this is handled automatically)
* Number of times to loop the victim program  
Once the user has specified those parameters within the terminal window, the tool takes control, booting the appropriate DomUs associated with the cores chosen, starting the interference generation, and running the victim program. Once the victim program has run the specified number of times, the tool returns and the test is complete.
The final test option, batch mode, allows the user to write the above parameters into a YAML file and execute multiple tests sequentially. This mode is useful for running many different combinations of base programs to generate a large number of test results with minimal user interaction. An example of the expected syntax may be observed in `test.yaml`.

## Analyzing Test Results
Once the user has completed their desired number of test runs using one of the two available modes, it is necessary to perform statistical analysis on the resultant metrics in order to generate some insights. This is achieved with a separate Python file, named yaml\_parser.py. In order to use this file, the user needs the matplotlib and yaml Python packages installed on their host system. The user should first remove the SD card from their test board and attach it to their host machine. Test results are stored in the directory `[root partition]/[friendly test name]` on the SD card. Given the way the YAML parser works, data analysis can only be done for one group of runs at a time, for instance `[base run, 1 core interference, 2 core interference, etc.]`. The user should edit the data\_dirs array to point to each of the directories that contains results to a corresponding group of runs. Once data_dirs has been updated, the user should run the program, which will aggregate all the data collected from the base program in each of the directories specified, and provide the average, worst-case, and standard deviation of the execution time from the data in each directory. It will also plot the execution times for each run in the dataset for visualization purposes.

