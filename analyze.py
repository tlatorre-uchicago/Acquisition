import h5py
import numpy as np

def get_times(x, data):
    min = np.min(data,axis=-1)
    threshold = 0.4*min
    return x[np.argmin(data > threshold[:,np.newaxis])]

def get_window(x, data):
    t = get_times(x,data)
    mean_hit_time = np.mean(t)
    return np.searchsorted(x,[mean_hit_time-10,mean_hit_time+100])

def integrate(x, data):
    """
    Integrate all waveforms in `data` with times `x`.
    """
    a, b = get_window(x,data)
    # i = v/r
    # divide by 50 ohms to convert to a charge
    return -np.trapz(data[a:b],x=x[a:b])/50.0/1000.0
    

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Analyze data from the Agilent scope')
    parser.add_argument('filenames',nargs='+',help='input filenames (hdf5 format)')
    parser.add_argument('-o','--output', default=None, help='output file name', required=True)
    args = parser.parse_args()

    charge = {}
    for filename in args.filenames:
        with h5py.File(filename) as f:
            x = f.attrs['xorg'] + np.linspace(0,f.attrs['xinc']*f.attrs['points'],f.attrs['points'])
            for channel in f:
                charge[channel] = integrate(x,f[channel])

    for name in charge:
        plt.hist(charge[name],bins=100)
    plt.xlabel("Charge (pC)")
    plt.show()
