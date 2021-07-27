from __future__ import print_function
import sys
import os
import time
import shutil
import datetime
import visa
from itertools import count
import json

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
        values[setting] = dpo.query('%s?' % setting)
    return values

def set_settings(dpo, settings):
    for key, value in settings.iteritems():
        dpo.write('%s %s' % key, value)

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Take data from the Agilent scope')
    parser.add_argument('-n','--numEvents', type=int, default=500, help='number of events')
    parser.add_argument('-r','--runNumber', type=int, default=None, help='run number')
    parser.add_argument('--sampleRate', type=float, default=20, help='Sampling rate in GHz (default 20)', required=True)
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
    args = parser.parse_args()

    if args.format not in ('h5','bin'):
        print("format must be either 'h5' or 'bin'",file=sys.stderr)
        exit(1)

    if args.trigSlope not in ("POSitive","NEGative"):
        print("trigSlope must be one of either 'POSitive' or 'NEGative'")
        exit(1)

    # establish communication with dpo
    rm = visa.ResourceManager("@py")
    dpo = rm.open_resource('TCPIP::%s::INSTR' % args.ip_address)

    settings = get_settings(dpo)

    dpo.timeout = 3000000
    dpo.encoding = 'latin_1'

    print("*idn? = %s" % dpo.query('*idn?')))

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

    with open("run%i_settings.json" % args.runNumber,'w') as f:
        json.dump(settings,f)

    dpo.write(':STOP;*OPC?')

    # percent of screen location
    # FIXME: Do we need this next line?
    #dpo.write(':TIMebase:REFerence:PERCent 50')
    if args.sampleRate:
        dpo.write(':ACQuire:SRATe:ANALog {}'.format(args.sampleRate*1e9))
    # offset
    if args.timeoffset:
        dpo.write(':TIMebase:POSition {}'.format(args.timeoffset*1e-9))
    # fast frame/segmented acquisition mode
    dpo.write(':ACQuire:MODE SEGMented')
    # number of segments to acquire
    dpo.write(':ACQuire:SEGMented:COUNt {}'.format(args.numEvents))
    # interpolation is set off (otherwise its set to auto, which cause errors downstream)
    dpo.write(':ACQuire:INTerpolate 0')

    dpo.write(':ACQuire:BANDwidth 5.E8')

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
    time.sleep(2)

    dpo.write('*CLS;:SINGle')
    start = time.time()
    end_early = False
    for i in count():
        if i % 10 == 0:
            print("",end='')

        if int(dpo.query(':ADER?')) == 1: 
            print("\nAcquisition complete")
            break
        else:
            time.sleep(0.1)
            if args.timeout is not None and time.time() - start > args.timeout:
                end_early = True
                dpo.write(':STOP;*OPC?')
                print()
                break

    end = time.time()

    duration = end - start
    trigRate = float(args.numEvents)/duration

    if not end_early:
        print("Run duration: %0.2f s. Trigger rate: %.2f Hz\n" % (duration,trigRate))
    else:
        print("Run duration: %0.2f s. Trigger rate: unknown\n" % (duration))

    output_path = 'C:\\Users\\Public\\'
    # save all segments (as opposed to just the current segment)
    dpo.write(':DISK:SEGMented ALL')
    print(dpo.query('*OPC?'))
    print("Ready to save all segments")
    time.sleep(0.5)
    for i in range(1,5):
        print("Saving Channel %i waveform" % i)
        dpo.write(':DISK:SAVE:WAVeform CHANnel%i %sWavenewscope_CH1_run%s",%s,ON' % (i,output_path,args.runNumber,args.format))
        print(dpo.query('*OPC?'))
        time.sleep(1)

    dpo.write(':ACQuire:MODE RTIMe')

    set_settings(dpo,settings)

    dpo.close()
