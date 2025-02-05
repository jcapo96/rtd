import matplotlib.pyplot as plt

plt.style.use("style.mplstyle")

def plot_temp_evolution(
    data=None, data_err=None, channel=None,
    tmin=77, tmax=350, tmax_err=5e-2,
    axes=None, marker=".", linestyle="", color="tab:blue"):
    if data_err is not None:
        data_plot = data.loc[(data[channel]>tmin)&(data[channel]<tmax)&(data_err[channel]<tmax_err)]
        data_plot_err = data_err.loc[data_plot.index]
    elif data_err is None:
        data_plot = data.loc[(data[channel]>tmin)&(data[channel]<tmax)]

    if data_err is None:
        axes.plot(data_plot.index.to_numpy(),
                  data_plot[channel].to_numpy(),
                  marker=marker, linestyle=linestyle, color=color,
                  label=f"{channel}")
    elif data_err is not None:
        axes.errorbar(data_plot.index.to_numpy(),
                  data_plot[channel].to_numpy(),
                  yerr=data_plot_err[channel].to_numpy(),
                  fmt=marker, linestyle=linestyle, color=color,
                  label=f"{channel}")
    plt.xticks(rotation=45)
    return axes