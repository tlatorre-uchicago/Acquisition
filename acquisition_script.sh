#!/bin/bash
for run in  {1..200}
do
	echo "run number: " ${run}
	# NaI and LYSO, 20210311, longer horizontal window for longer decay time of NaI
	#python acquisition.py --numEvents 200 --trigCh 2 --trig -0.2 --sampleRate 10 --horizontalWindow 2000 --timeoffset 600 --vScale1 0.04 --vScale2 0.2 --vScale3 0.04 --vPos1 3 --vPos2 3 --vPos3 3 --runNumber ${run}

	# lyso for both PMT, 20210309
	python acquisition.py --numEvents 1000 --trigCh 2 --trig -0.2 --sampleRate 10 --horizontalWindow 1000 --timeoffset 0 --vScale1 0.04 --vScale2 0.2 --vScale3 0.04 --vPos1 3 --vPos2 3 --vPos3 3 --runNumber ${run}
done
