import h5py
import numpy as np
import matplotlib.pyplot as plt

def get_times(x, data):
    """
    Returns the times at which the waveforms in `x` cross 40% of their minimum
    value.
    """
    min = np.min(data,axis=-1)
    threshold = 0.4*min
    return x[np.argmin(data > threshold[:,np.newaxis],axis=-1)]

def get_window(x, data):
    """
    Returns the indices start and stop over which you should integrate the
    waveforms in `x`. The window is found by calculating the median hit time
    for all pulses in `x` and then going back 10 ns and forward 100 ns.
    """
    t = get_times(x,data)
    mean_hit_time = np.median(t)
    a, b = np.searchsorted(x,[mean_hit_time-10,mean_hit_time+100])
    if a < 0:
        a = 0
    if b > len(x) - 1:
        b = len(x) - 1
    return a, b

def integrate(x, data):
    """
    Integrate all waveforms in `data` with times `x`.
    """
    a, b = get_window(x,data)
    # i = v/r
    # divide by 50 ohms to convert to a charge
    return -np.trapz(data[:,a:b],x=x[a:b])*1000/50.0

if __name__ == '__main__':
    from argparse import ArgumentParser
    import ROOT

    parser = ArgumentParser(description='Analyze data from the Agilent scope')
    parser.add_argument('filenames',nargs='+',help='input filenames (hdf5 format)')
    parser.add_argument('-o','--output', default=None, help='output file name', required=True)
    args = parser.parse_args()

    plt.figure()
    charge = {}
    for filename in args.filenames:
        with h5py.File(filename) as f:
            x = f.attrs['xorg'] + np.linspace(0,f.attrs['xinc']*f.attrs['points'],f.attrs['points'])
            x *= 1e9
            for channel in f:
                charge[channel] = integrate(x,f[channel])
                plt.plot(x,f[channel][:10].T)
                a, b = get_window(x,f[channel])
                plt.axvline(x[a])
                plt.axvline(x[b])

    f = ROOT.TFile(args.output,"recreate")
    for channel in charge:
        h = ROOT.TH1D(channel,"Charge Integral for %s" % channel,110,-10,110)
        for x in charge[channel]:
            h.Fill(x)
        h.Write()
    f.Close()

    plt.figure()
    for name in charge:
        plt.hist(charge[name],bins=100,histtype='step',label=name)
    plt.xlabel("Charge (pC)")
    plt.legend()
    plt.show()
