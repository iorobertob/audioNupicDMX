![Alt text](https://cloud.githubusercontent.com/assets/11702381/11360485/cb342456-9239-11e5-9c1d-c5068b68eb88.png "Optional title")

# audioNupicDMX
This work takes Audio from a Microphone, processes it with a Machine Learning algorithm in such way that Anomalies are detected in the sound. This anomalies are used to generate one single, or several values, ranging between 0 and 255 to send over a DMX bus in order to control lights on a custom fashion. The system is programmed in Python, and it uses version 2.7 specifically. 

Anomaly, referring to some values of the sound input that divert from what has been expected, or normal. 

The Machine Learning algorithm used is a Hierarchical Temporal Memory (HTM) implemented in the project called NuPIC, from Numenta. This is an open source project found in this respository. [NuPIC](https://github.com/numenta/nupic) is the state of the art in computer models of the human brain, designed to work in the same way the Neocortex does. More about this in the NuPIC section. 

The inspiration for this comes from a work by artist/cybernitician Gordon Pask called Musicolour, which took audio and gave visual output playing with concepts like learning machines, memory elements, repetitive input, and the reaction of the system to such repetitions, growing less reactive to repetition than to novel input. All this being analogue and here ported to contemporary digital technology and current machine learning systems. 

## to Install
Copy only the _install.sh file, run it within the folwer you want to work in by typing

$ ./_install.sh

this should install all dependencies, clone this respository and set go into that folder with the terminal. 

After that the main file AND_6.py can be called with:

$ python AND_6.py

## hardware Requirements

*[Enttec DMX USB Pro](https://www.enttec.com/?main_menu=Products&pn=70304&show=description)
* Find the name of the current connected controller by typing in Terminal: ls /dev/tty.*

*A microphone input

*A DMX Fixture.

*MAC OSX 10.10 Yosemite or higher
