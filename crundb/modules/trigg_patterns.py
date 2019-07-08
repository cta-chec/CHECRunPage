try:
    import dashi

    dashi.visual()
except:
    print(
        "\u001b[31mThe dashi package, which is needed for the histograms, seems to be missing!\u001b[0m"
    )
    print(
        "Try installing it with: `pip install https://github.com/emiddell/dashi/zipball/master`"
    )
    raise ImportError(
        "\u001b[31mThe dashi package, which is needed for the histograms, seems to be missing!\u001b[0m\n"
        "Try installing it with: `pip install https://github.com/emiddell/dashi/zipball/master`"
    )

import numpy as np
from matplotlib import pyplot as plt
from ssdaq.data.io import DataReader
from ssdaq.core.utils import get_si_prefix

from CHECLabPy.plotting.setup import Plotter
from CHECLabPy.plotting.camera import CameraImage
from CHECLabPy.utils.mapping import get_superpixel_mapping

from target_calib import CameraConfiguration
from CHECLabPy.utils.mapping import get_clp_mapping_from_tc_mapping
import datetime
from crundb.utils import savefig_to_buffer, make_field


class ImagePlotter(Plotter):
    def __init__(self, mapping):

        sp_mapping = get_superpixel_mapping(mapping)
        self.fig = plt.figure(figsize=(10, 5))
        self.ax_trigger = self.fig.add_subplot(1, 1, 1)

        self.ci_trigger = self.create_image(
            sp_mapping, ax=self.ax_trigger, clabel="Trigger"
        )

        self.n_superpixels = sp_mapping.index.size
        sp_zero = np.zeros(self.n_superpixels, dtype=bool)
        self.ci_trigger.image = sp_zero

    @staticmethod
    def create_image(mapping, ax, clabel):
        ci = CameraImage.from_mapping(mapping, ax=ax)
        ci.add_colorbar(clabel, pad=0)
        return ci

    def set_image(self, title, trigger):
        self.ci_trigger.image = trigger

        self.fig.suptitle(title)


from crundb.core.submitplugin import SubmitPluginBase


class TriggerPatternSubmit(SubmitPluginBase):
    @property
    def short_name(self):
        return "triggpat"

    def generate_submit(self, files):
        return self.trigger_pattern_diagnostics(files, save=False, entry=True)

    def trigger_pattern_diagnostics(self, files, save, entry=False):
        run_name = files.run
        if files["trigfile"] is not None:
            filename = files["trigfile"][0]
        else:
            return None
        reader = DataReader(filename)
        print(reader)
        triggs = reader[:]
        mean_rate = len(triggs) / (triggs[-1].TACK - triggs[0].TACK) * 1e9
        print("Mean trigger rate {}{}Hz".format(*get_si_prefix(mean_rate)))
        print("Total number of trigger patterns", len(triggs))
        tacks = []
        nSP = []
        ntriggSP = []
        heatmap = []
        trigg_phase = []
        from ssdaq.data._dataimpl.trigger_format import get_bptrigg2SP_mapping

        m1 = get_bptrigg2SP_mapping()
        last_uc_ev = 0
        missed_counter = []
        for t in triggs:
            if last_uc_ev != 0 and last_uc_ev + 1 != t.uc_ev:
                missed_counter.append(t.uc_ev - last_uc_ev)
            else:
                missed_counter.append(0)
            last_uc_ev = t.uc_ev
            trigg = t.trigg
            tacks.append(t.TACK)
            nSP.append(np.sum(t.trigg_union))
            ntriggSP.append(np.sum(trigg))
            trigg_phase.append(t.trigg_phase)
            # if np.sum(t.trigg_union) < 200:
            heatmap.append(trigg[m1])
        heatmap = np.array(heatmap)
        t0 = tacks[0]
        run_length = tacks[-1] - tacks[0]
        ntriggSP = np.array(ntriggSP)
        nSP = np.array(nSP)
        tacks = np.array(tacks, dtype=np.uint64)
        timeedges = np.linspace(0, run_length, int(run_length / 1e9) + 1)
        nSPedges = np.logspace(0, 2.6, 100)
        tack_dt = np.diff(tacks)
        triggdt = dashi.histogram.hist1d(
            np.logspace(np.log10(np.min(tack_dt)), np.log10(np.max(tack_dt)), 100)
        )
        triggdt.fill(tack_dt)

        triggTotSP = dashi.histogram.hist1d(nSPedges)
        triggTotSP.fill(np.array(nSP))
        triggSP = dashi.histogram.hist1d(nSPedges)
        triggSP.fill(np.array(ntriggSP))

        triggRate = dashi.histogram.hist1d(timeedges)
        triggRate.fill(tacks - t0)
        triggRate.binedges[:] /= 1e9
        missedPackets = dashi.histogram.hist1d(timeedges)
        missedPackets.fill(tacks - t0, np.array(missed_counter))
        missedPackets.binedges[:] /= 1e9

        t_phases = np.log2(np.array(trigg_phase))
        triggerphase = dashi.histogram.hist1d(
            np.linspace(
                np.min(t_phases),
                np.max(t_phases) + 1,
                np.max(t_phases) - np.min(t_phases) + 2,
            )
            - 0.5
        )
        triggerphase.fill(t_phases)

        fig = plt.figure(figsize=(11, 7))
        fig.suptitle("{} mean rate {}{}Hz".format(run_name, *get_si_prefix(mean_rate)))
        ax1 = fig.add_subplot(2, 2, 1)
        triggdt.line()
        plt.xscale("log")
        plt.yscale("log")
        plt.xlabel("TACK dt (ns)")
        plt.ylabel("number of triggers")

        ax2 = fig.add_subplot(2, 2, 2)
        triggTotSP.line(label="Total number of SPs (union)")
        triggSP.line(label="Triggered SPs")
        plt.xscale("log")
        plt.yscale("log")
        plt.xlabel("number of SPs")
        plt.ylabel("number of triggers")
        plt.legend(fontsize=6)

        ax3 = fig.add_subplot(2, 2, 3)
        color = "tab:red"
        triggRate.line(color=color)
        plt.xlabel("Time since run start (s)")
        plt.ylabel("Instantious trigger rate (Hz)", color=color)
        ax3twin = ax3.twinx()  # instantiate a second axes that shares the same x-axis

        color = "tab:blue"
        ax3twin.set_ylabel(
            "number of missed packets", color=color
        )  # we already handled the x-label with ax1
        missedPackets.line(color=color)
        # ax3twin.plot(, data2, color=color)
        ax3twin.tick_params(axis="y", labelcolor=color)

        ax3 = fig.add_subplot(2, 2, 4)
        plt.errorbar(
            triggerphase.bincenters,
            triggerphase.bincontent,
            yerr=triggerphase.binerror,
            xerr=triggerphase.binwidths / 2,
            elinewidth=1,
            linestyle="",
            fmt="o",
        )
        plt.xlabel("Trigger phase")
        plt.ylabel("Number of triggers")
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        c = CameraConfiguration("1.1.0")
        m = c.GetMapping()
        p_image = ImagePlotter(get_clp_mapping_from_tc_mapping(m))
        p_image.set_image(
            "{} Trigger heat map No Flasher correction".format(
                run_name, *get_si_prefix(mean_rate)
            ),
            np.sum(heatmap, axis=0) / len(triggs),
        )
        p_image2 = ImagePlotter(get_clp_mapping_from_tc_mapping(m))
        p_image2.set_image(
            "{} Trigger heat map with Flasher correction".format(
                run_name, *get_si_prefix(mean_rate)
            ),
            np.sum(heatmap[nSP < 200], axis=0) / len(triggs),
        )
        p_image3 = ImagePlotter(get_clp_mapping_from_tc_mapping(m))
        p_image3.set_image(
            "{} Triggered SPs".format(run_name, *get_si_prefix(mean_rate)),
            np.sum(heatmap, axis=0) > 0,
        )
        if save:
            fig.savefig(f"{run_name}_trigpat_diag.png")
            print(f"Figure saved to: {run_name}_trigpat_diag.png")
            p_image.save(f"{run_name}_trig_heatmap_noflashcorr.png")
            p_image2.save(f"{run_name}_trig_heatmap_withflashcorr.png")
            p_image3.save(f"{run_name}_trig_sps.png")
        elif entry:
            start_time = reader.timestamp
            date = start_time.date()
            dt = start_time - datetime.datetime(date.year, date.month, date.day)
            if dt.seconds < 3600 * 6:
                date = date.replace(day=date.day - 1)

            dbentry = {
                "RUN": run_name,
                "modstats": {
                    "obsdate": date,
                    "run_start": start_time.time(),
                    "run_start_timestamp": reader.timestamp,
                    "ntriggs": reader.n_entries + int(np.sum(missedPackets.bincontent)),
                    "run_length": datetime.timedelta(seconds=run_length * 1e-9),
                    "rate": mean_rate,
                },
                "modules": {
                    "figures": {
                        "trigpat_diag": savefig_to_buffer(fig),
                        "trig_heatmap_noflashcorr": savefig_to_buffer(p_image.fig),
                        "trig_heatmap_withflashcorr": savefig_to_buffer(p_image2.fig),
                        "trig_sps": savefig_to_buffer(p_image3.fig),
                    },
                    "stats": {
                        "number of triggers": make_field(
                            "number of triggers",
                            int(np.sum(missedPackets.bincontent)) + reader.n_entries,
                        ),
                        "mean rate": "{}{}Hz".format(*get_si_prefix(mean_rate)),
                        "lost trigger packets": int(np.sum(missedPackets.bincontent)),
                        "max rate": "{}{}Hz".format(
                            *get_si_prefix(np.max(triggRate.bincontent))
                        ),
                        "min rate": "{}{}Hz".format(
                            *get_si_prefix(np.min(triggRate.bincontent))
                        ),
                        "number of triggering SPs": int(
                            np.sum(p_image3.ci_trigger.image)
                        ),
                        "number of nontriggering SPs": 512
                        - int(np.sum(p_image3.ci_trigger.image)),
                        "fraction of triggering SPs": "{0:.2f}%".format(
                            np.sum(p_image3.ci_trigger.image) / 512.0 * 100
                        ),
                    },
                    "title": "Trigger patterns",
                },
            }

            return dbentry
