from ssdaq.data.io import SSDataReader
from ssm.core import badsspixs
import numpy as np
from crundb.core.submitplugin import SubmitPluginBase
from matplotlib import pyplot as plt
from crundb.utils import savefig_to_buffer,make_field
from crundb.core.sval import SVal
class SlowSignalSubmit(SubmitPluginBase):
    @property
    def short_name(self):
        return "slowsig"

    def generate_submit(self, files):
        badpixs = badsspixs.get_badpixs()
        run_name = files["Run"]
        #Get correct file type
        if files['ssfile'] is not None:
            filename = files['ssfile'][0]
        else:
            #if no file found
            return None

        # Read data
        reader = SSDataReader(filename)
        total_bright = []
        av_total_bright = []
        time = []
        res = []
        for r in reader.read():
            r = r.flatten()
            if np.any(np.isnan(r)):
                continue
            r[badpixs] = np.nan
            res.append(r)
            total_bright.append(np.nansum(r))#/(r.shape[0]-np.sum(np.isnan(r))))
            av_total_bright.append(np.nansum(r)/(r.shape[0]-np.sum(np.isnan(r))))
            time.append(reader.cpu_t)
        reader.close_file()
        res = np.array(res)
        ntime = np.array(time)
        #Make a plot
        fig = plt.figure(figsize=(11, 7))
        plt.plot(ntime-ntime[0],av_total_bright)
        total_bright =np.array(total_bright)
        plt.title(f"Average slow signal amplitude during {run_name}")
        plt.ylabel('Average slow signal amplitude (mV)')
        plt.xlabel('Time since run start (s)')
        # make a database entry
        dbentry = {
                "RUN": run_name,#Not really necessary
                "modstats":{},# Here goes general stats that
                              # might be used by the server to make
                              # a run summary (needs to be configured in `pageconf.yaml)
                "modules": {#Here goes the data which makes up the entry in the run page
                        "figures": {# Figures
                            "ssamplitude_vs_time": savefig_to_buffer(fig),

                            },
                        "title": "Slow Signal",# The heading to be used for this section
                        "stats":{'nframes': make_field('Number of good frames',SVal(int(res.shape[0]))),
                                 "rate":make_field('Frame rate',SVal(res.shape[0]/(ntime[-1]-ntime[0]),'Hz')),
                                 "maxamp":make_field('Max amplitude',SVal(np.max(av_total_bright)*1e-3,'V',stickyprefix='m')),
                                 "minamp":make_field('Min amplitude',SVal(np.min(av_total_bright)*1e-3,'V',stickyprefix='m')),
                                 "avamp":make_field('Min amplitude',SVal(np.mean(av_total_bright)*1e-3,'V',stickyprefix='m'))}# Stats list
                        },
                }
        plt.close(fig)

        return dbentry