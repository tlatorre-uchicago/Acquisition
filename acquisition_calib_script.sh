#!/bin/bash
for run in  {21..30}
do
	echo "run number: " ${run}
	#self trigger for calibration channel 1
	#python acquisition.py --numEvents 10000 --trigCh 1 --trig -0.02 --sampleRate 10 --horizontalWindow 1000 --timeoffset 200 --vScale1 0.04 --vScale2 0.2 --vScale3 0.04 --vPos1 3 --vPos2 3 --vPos3 3 --runNumber ${run}
	python acquisition.py --numEvents 10000 --trigCh 3 --trig -0.02 --sampleRate 10 --horizontalWindow 1000 --timeoffset 200 --vScale1 0.04 --vScale2 0.2 --vScale3 0.04 --vPos1 3 --vPos2 3 --vPos3 3 --runNumber ${run}
	#self trigger for calibration channel 3 NaI, longer horizontal window, less events, smaller vScale
	#python acquisition.py --numEvents 5000 --trigCh 3 --trig -0.006 --sampleRate 10 --horizontalWindow 2000 --timeoffset 600 --vScale1 0.04 --vScale2 0.2 --vScale3 0.03 --vPos1 3 --vPos2 3 --vPos3 3 --runNumber ${run}




done
