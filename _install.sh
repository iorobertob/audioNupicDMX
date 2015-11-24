
# Install Mac's Command Line Developer Tools 
touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress;
PROD=$(softwareupdate -l |
  grep "\*.*Command Line" |
  head -n 1 | awk -F"*" '{print $2}' |
  sed -e 's/^ *//' |
  tr -d '\n')
softwareupdate -i "$PROD" -v;
# Go to Nupic website
# https://github.com/numenta/nupic

# Follos instructions, install nupic by typing in the teminal
# anywhere, i.e. /Users/USERNAME/
# --user flat to install in a non sytem location  
#pip install nupic --user

#
 #if pip is not installed
# python --version 
# to check what python we have
sudo easy_install pip

# again type
#pip install nupic --user

# ERROR MESSAGE might show asking to Install Command Line Developer Tools
# Press Install - 5 min.

# The sofware was installed. - Done
pip install nupic --user
# 5 min.

# Clond the Nupid repository
git clone https://github.com/numenta/nupic.git

# Install PyTest
sudo pip install pytest 


#Install Homebrew
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

#Install PortAudio
brew install portaudio


# Install PyAudio
pip install PortAudio --user

#Install PySerial
pip install pySerial --user


# Clone the projec repository
git clone https://github.com/iorobertob/audioNupicDMX.git

# Go to project folder
cd audioNupicDMX

# RUN
#python AND_6.py
