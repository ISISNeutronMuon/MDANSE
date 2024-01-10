import numpy as np
import matplotlib.pyplot as mpl


def read_array_data(fname, axes_in_array=True, transpose=False):
    x_axis = []
    y_axis = []
    data = []
    counter = 0
    with open(fname, "r") as source:
        for line in source:
            toks = line.split()
            if len(toks) < 1:
                continue
            if "#" in toks[0]:
                continue
            nums = np.array([float(x) for x in toks])
            if counter == 0:
                y_axis = nums[1:]
            else:
                x_axis.append(nums[0])
                data.append(nums[1:])
            counter += 1
    if transpose:
        data = np.array(data).T
        temp = np.array(y_axis)
        y_axis = np.array(x_axis)
        x_axis = np.array(temp)
    else:
        data = np.array(data)
        x_axis = np.array(x_axis)
        y_axis = np.array(y_axis)
    return data, x_axis, y_axis


data1, xs1, ys1 = read_array_data("reference_sqft_total_fromplotter.txt")
data2, xs2, ys2 = read_array_data("s(q,f)_total_sigma1.dat", transpose=True)

datadict1, datadict2 = {}, {}
keys = []

for n, val in enumerate(ys1):
    datadict1[val] = data1[:, n]
    keys.append(val)

for n, val in enumerate(ys2):
    datadict2[val] = data2[:, n]
    keys.append(val)

keys = sorted(set(keys))

fig = mpl.figure(figsize=[12.0, 8.0], dpi=150, frameon=False)

for k in keys:
    fig.clear()
    axes = fig.add_subplot(111)
    axes2 = axes.twinx()
    axes.plot(xs1, datadict1[k], "k", label="Reference from plotter")
    axes2.plot(xs2, datadict2[k], "r", label="From MDANSE ASCII output")
    axes.set_title("At y=" + str(k))
    axes.legend(loc=0)
    mpl.savefig("comparison_at_" + str(k) + ".png")
