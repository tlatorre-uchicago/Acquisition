from __future__ import print_function
import sys
import os
import time
import shutil
import datetime
import pyvisa as visa
from itertools import count
import json
import numpy as np
import h5py

SETTINGS = [\
    ':TIMebase:RANGe',
    ':ACQuire:SRATe:ANALog',
    ':TIMebase:POSition',
    ':ACQuire:MODE',
    ':ACQuire:INTerpolate',
    ':CHANnel1:SCALe',
    ':CHANnel2:SCALe',
    ':CHANnel3:SCALe',
    ':CHANnel4:SCALe',
    ':CHANnel1:OFFSet',
    ':CHANnel2:OFFSet',
    ':CHANnel3:OFFSet',
    ':CHANnel4:OFFSet',
    ':ACQuire:INTerpolate',
    ':TRIGger:MODE',
    ':TRIGger:EDGE:SOURce',
    ':TRIGger:LEVel',
    ':TRIGger:EDGE:SLOPe',
]

def get_settings(dpo):
    values = {}
    for setting in SETTINGS:
        if setting == ':TRIGger:LEVel':
            for channel in ['CHANnel%i' % i for i in range(1,5)] + ['AUX']:
                values["%s %s," % (setting,channel)] = dpo.query('%s? %s' % (setting,channel))
        else:
            values[setting] = dpo.query('%s?' % setting)
    return values

def set_settings(dpo, settings):
    for key, value in settings.iteritems():
        dpo.write('%s %s' % (key, value))

def is_done(dpo):
    return int(dpo.query("*OPC?")) == 1

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Take data from the Agilent scope')
    parser.add_argument('-n','--numEvents', type=int, default=500, help='number of events')
    parser.add_argument('-r','--runNumber', type=int, default=None, help='run number')
    parser.add_argument('--sampleRate', type=float, default=None, help='Sampling rate in GHz')
    parser.add_argument('--trigCh', type=str, default=None, help="trigger Channel (1,2,3,4, or 'AUX')")
    parser.add_argument('--trig', type=float, default=None, help='trigger value in V')
    parser.add_argument('--trigSlope', default=None, help='trigger slope should be "POSitive or NEGative"')
    parser.add_argument('--vScale1', type=float, default=None, help='Vertical scale ch. 1, (volts/div)')
    parser.add_argument('--vScale2', type=float, default=None, help='Vertical scale ch. 2, (volts/div)')
    parser.add_argument('--vScale3', type=float, default=None, help='Vertical scale ch. 3, (volts/div)')
    parser.add_argument('--vScale4', type=float, default=None, help='Vertical scale ch. 4, (volts/div)')
    parser.add_argument('--vOffset1', type=float, default=None, help='Vertical Offset ch. 1, (volts)')
    parser.add_argument('--vOffset2', type=float, default=None, help='Vertical Offset ch. 2, (volts)')
    parser.add_argument('--vOffset3', type=float, default=None, help='Vertical Offset ch. 3, (volts)')
    parser.add_argument('--vOffset4', type=float, default=None, help='Vertical Offset ch. 4, (volts)')
    parser.add_argument('--timeoffset', type=float, default=None, help='Offset to compensate for trigger delay (ns). This is the delta T between the center of the acquisition window and the trigger.')
    parser.add_argument('--timeout', type=float, default=None, help='Max run duration [s]')
    parser.add_argument('--format', default='bin', help='output format (h5 or bin)')
    parser.add_argument('--ip-address', help='ip address of scope', required=True)
    parser.add_argument('--settings', default=None, help='json file with settings', required=False)
    parser.add_argument('-o','--output', default=None, help='output file name', required=True)
    args = parser.parse_args()

    if args.format not in ('h5','bin'):
        print("format must be either 'h5' or 'bin'",file=sys.stderr)
        exit(1)

    if args.trigSlope and args.trigSlope not in ("POSitive","NEGative"):
        print("trigSlope must be one of either 'POSitive' or 'NEGative'")
        exit(1)

    # establish communication with dpo
    rm = visa.ResourceManager()
    dpo = rm.open_resource('TCPIP::%s::INSTR' % args.ip_address)

    print(dir(dpo))

    settings = get_settings(dpo)

    dpo.timeout = 3000000
    dpo.encoding = 'latin_1'

    print("*idn? = %s" % dpo.query('*idn?').strip())

    if args.settings:
        with open(args.settings) as f:
            settings = json.load(f)
        print("loading settings from %s" % args.settings)
        set_settings(dpo,settings)

    # increment the last runNumber by 1
    if args.runNumber is None:
        if os.path.exists('runNumber.txt'):
            with open('runNumber.txt','r') as file:
                args.runNumber = int(file.read())+1

            with open('runNumber.txt','w') as file:
                file.write("%i" % args.runNumber)
        else:
            args.runNumber = 1

            with open('runNumber.txt','w') as file:
                file.write("%i" % args.runNumber)

    print("Saving settings to run%i_settings.json" % args.runNumber)

    with open("run%i_settings.json" % args.runNumber,'w') as f:
        json.dump(settings,f)

    dpo.write(':STOP')

    while not is_done(dpo):
        time.sleep(0.1)

    if args.sampleRate:
        dpo.write(':ACQuire:SRATe:ANALog {}'.format(args.sampleRate*1e9))
    # offset
    if args.timeoffset:
        dpo.write(':TIMebase:POSition {}'.format(args.timeoffset*1e-9))

    if args.vScale1:
        dpo.write(':CHANnel1:SCALe %.2f'.format(args.vScale1))
    if args.vScale2:
        dpo.write(':CHANnel2:SCALe %.2f'.format(args.vScale2))
    if args.vScale3:
        dpo.write(':CHANnel3:SCALe %.2f'.format(args.vScale3))
    if args.vScale4:
        dpo.write(':CHANnel4:SCALe %.2f'.format(args.vScale4))

    if args.vOffset1:
        dpo.write(':CHANnel1:OFFSet %.2f'.format(args.vOffset1))
    if args.vOffset2:
        dpo.write(':CHANnel2:OFFSet %.2f'.format(args.vOffset2))
    if args.vOffset3:
        dpo.write(':CHANnel3:OFFSet %.2f'.format(args.vOffset3))
    if args.vOffset4:
        dpo.write(':CHANnel4:OFFSet %.2f'.format(args.vOffset4))

    dpo.write(':TRIGger:MODE EDGE;')

    if args.trigCh:
        if args.trigCh == "AUX":
            pass
        else:
            try:
                args.trigCh = 'CHANnel%i' % args.trigCh
            except TypeError:
                print("trigger channel must be either 1, 2, 3, 4, or 'AUX'",file=sys.stderr)
                sys.exit(1)

        dpo.write(':TRIGger:EDGE:SOURce %s' % args.trigCh)

    if args.trigCh and args.trig:
        dpo.write(':TRIGger:LEVel %s, %f' % (args.trigCh, args.trig))

    if args.trigSlope:
        dpo.write(':TRIGger:EDGE:SLOPe %s;' % args.trigSlope)

    # configure data transfer settings
    while not is_done(dpo):
        time.sleep(0.1)

    print("done setting up")

    dpo.write(":system:header off")
    dpo.write(":WAVeform:format ASCII")
    xinc = float(dpo.query(":WAVeform:xincrement?"))
    xorg = float(dpo.query(":WAVeform:xorigin?"))
    points = float(dpo.query(":WAVeform:points?"))

    # x = xorg + np.linspace(0,xinc*n,n)
    f = h5py.File(args.output,"w")
    f.attrx['xinc'] = xinc
    f.attrx['xorg'] = xorg
    f.attrx['points'] = points

    try:
        enabled_channels = []
        for i in range(1,5):
            if int(dpo.query(":CHANnel%i:display?" % i)) == 1:
                enabled_channels.append(i)
            f.create_dataset("channel%i" % i, (args.numEvents, n), dtype='f4')

        for i in range(args.numEvents):
            if i % 10 == 0:
                print(".",end='')
                sys.stdout.flush()

            dpo.write(':digitize')
            for j in enabled_channels:
                dpo.write(":WAVeform:source channel%i" % j)
            f['channel%i' % j][i] = np.array(map(float,dpo.query(":WAVeform:DATA?").split(',')[:-1]))
    finally:
        f.close()

    dpo.write(':ACQuire:MODE RTIMe')

    set_settings(dpo,settings)

    dpo.close()
