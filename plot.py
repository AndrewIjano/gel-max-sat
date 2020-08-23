import matplotlib.pyplot as plt
import pandas as pd
import sys
import numpy as np
from scipy.interpolate import make_interp_spline, BSpline
import statistics as stat

SMOOTHING_FACTOR = 5

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: python3 plot.py <filename.csv>')
    else:
        dataset = sys.argv[1]
        df = pd.read_csv(dataset)
        print(df)
        gp = df.groupby(['Concepts count', 'Axioms count'])
        axioms_counts = [j for i, j in gp.groups.keys()]

        means = gp.mean()

        # plt.rcParams.update({'font.size': 16})
        fig, ax1 = plt.subplots()
        ax1.set_xlabel('m/n')
        ax1.set_title(
            f'GEL-MaxSAT: SAT proportion and time (w = {SMOOTHING_FACTOR})')

        sats_mean = means.get('SAT proportion mean').values
        sats_stdev = means.get('SAT proportion std').values

        smoothing_window = np.ones(SMOOTHING_FACTOR)/SMOOTHING_FACTOR

        def smooth_data(data): return np.convolve(
            data, smoothing_window, mode='valid')

        axioms_counts = smooth_data(axioms_counts)
        sats_mean = smooth_data(sats_mean)
        ax1.set_ylabel('%GEL-MaxSAT', color='b')
        ax1.plot(axioms_counts, sats_mean, color='b')

        ax2 = ax1.twinx()

        times_mean = means.get('Time mean').values
        times_stdev = means.get('Time std').values

        times_mean = smooth_data(times_mean)
        ax2.set_ylabel('time (s)', color='r')
        ax2.plot(axioms_counts, times_mean, color='r', ls='--')

        fig.tight_layout()
        plt.show()
