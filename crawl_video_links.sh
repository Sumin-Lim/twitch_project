#!/bin/bash

###########################################################################
## environment & variable setup
####### job customization
SBATCH -N 1
SBATCH -n 16
SBATCH -t 1:00:00
SBATCH -p normal_q
SBATCH -A <your account>
####### end of job customization
# end of environment & variable setup
###########################################################################
#### add modules:

git clone https://github.com/Sumin-Lim/twitch_project
cd twitch_project
module load Anaconda/2020.11
conda create -n twitch python=3.7 pip
source activate twitch
python -m pip install -r requirements.txt

module list
#end of add modules
###########################################################################
echo start load env and run python

python get_twitch_video.py

exit;
