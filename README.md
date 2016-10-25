![Alt text](https://cloud.githubusercontent.com/assets/11702381/11360485/cb342456-9239-11e5-9c1d-c5068b68eb88.png "Optional title")

# audioNupicDMX
-- AND_9 breaks the project into several class files

This work takes Audio from a Microphone, processes it with a Machine Learning algorithm in such way that Anomalies are detected in the sound. This anomalies are used to control DMX fxitures's colours brighness. It also reproduces WAV files in accordance to such Anomalies. The system is programmed in Python, and it uses version 2.7 specifically. 

Anomaly, referring to some values of the sound input that divert from what has been expected, or normal. 

The Machine Learning algorithm used is a Hierarchical Temporal Memory (HTM) implemented in the project called NuPIC, from Numenta. This is an open source project found in this respository. [NuPIC](https://github.com/numenta/nupic) is the state of the art in computer models of the human brain, designed to work in the same way the Neocortex does.

## to Install Dependencies and Clone this Rep
Copy only the _install.sh file, run it within the folder you want to work in by typing

$ chmod a+x _install.sh

$ ./_install.sh

this should install all dependencies, clone this respository and set go into that folder with the terminal. 

After that the main file AND_96.py can be called with:

$ python AND_96.py

## hardware Requirements

*[Enttec DMX USB Pro](https://www.enttec.com/?main_menu=Products&pn=70304&show=description)
* Find the name of the current connected controller by typing in Terminal: ls /dev/tty.*

*A microphone input

*A DMX Fixture.

*MAC OSX 10.10 Yosemite or higher
