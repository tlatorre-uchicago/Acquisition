import h5py
import numpy as np

def iqr(x):
    return np.percentile(x,75) - np.percentile(x,25)

def get_times(x, data, baseline=10):
    """
    Returns the times at which the waveforms in `x` cross 40% of their minimum
    value.
    """
    data = np.asarray(data)
    # Get the first 10 ns of every waveform to calculate the noise level
    noise = iqr(data[:,np.where(x < x[0] + baseline)[0]])
    # Get events with a pulse
    pulses = np.min(data,axis=-1) < -noise*5
    # Select events with pulses. If there are no matches (which might be the
    # case for the triggering channel), then don't apply the selection.
    if np.count_nonzero(pulses):
        data = data[pulses]
    min = np.min(data,axis=-1)
    threshold = 0.4*min
    return x[np.argmin(data > threshold[:,np.newaxis],axis=-1)]

def get_window(x, data, left=1, right=10):
    """
    Returns the indices start and stop over which you should integrate the
    waveforms in `x`. The window is found by calculating the median hit time
    for all pulses in `x` and then going back 10 ns and forward 100 ns.
    """
    data = np.asarray(data)
    t = get_times(x,data)
    mean_hit_time = np.median(t)
    a, b = np.searchsorted(x,[mean_hit_time-left,mean_hit_time+right])
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

def get_bins(x):
    """
    Returns bins for the data `x` using the Freedman Diaconis rule. See
    https://en.wikipedia.org/wiki/Freedman%E2%80%93Diaconis_rule.
    """
    bin_width = 2*iqr(x)/len(x)**(1/3.0)
    return np.arange(np.min(x),np.min(x),bin_width)

if __name__ == '__main__':
    from argparse import ArgumentParser
    import ROOT
    import matplotlib.pyplot as plt

    parser = ArgumentParser(description='Analyze data from the Agilent scope')
    parser.add_argument('filenames',nargs='+',help='input filenames (hdf5 format)')
    parser.add_argument('-o','--output', default=None, help='output file name', required=True)
    parser.add_argument('--sodium', default=False, action='store_true', help='flag to indicate data is from a sodium source')
    parser.add_argument('--plot', default=False, action='store_true', help='plot the waveforms and charge integral')
    args = parser.parse_args()

    charge = {}
    for filename in args.filenames:
        with h5py.File(filename) as f:
            x = f.attrs['xorg'] + np.linspace(0,f.attrs['xinc']*f.attrs['points'],f.attrs['points'])
            x *= 1e9
            for channel in f:
                if channel == 'settings':
                    continue
                charge[channel] = integrate(x,f[channel])
                if args.sodium:
                    a, b = get_window(x,f[channel],left=10,right=100)
                else:
                    a, b = get_window(x,f[channel])
                if args.plot:
                    plt.figure()
                    plt.plot(x,f[channel][:100].T)
                    plt.xlabel("Time (ns)")
                    plt.ylabel("Voltage (V)")
                    plt.title(channel)
                    plt.axvline(x[a])
                    plt.axvline(x[b])

    f = ROOT.TFile(args.output,"recreate")
    for channel in charge:
        bins = get_bins(charge[channel])
        h = ROOT.TH1D(channel,"Charge Integral for %s" % channel,len(bins),bins[0],bins[-1])
        for x in charge[channel]:
            h.Fill(x)
        h.Write()
        if args.plot:
            plt.figure()
            plt.hist(charge[channel],bins=bins,histtype='step',label=channel)
            plt.xlabel("Charge (pC)")
            plt.legend()
    f.Close()

    if args.plot:
        plt.show()
