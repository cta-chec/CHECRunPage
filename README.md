# CHECRunPage
This package is intended to generate a simple `sphinx` based run list web page. It consists of a submiter client that processes different types of run files to create run statistics and plots which are sent to a server modules which generates the webpage. 

## Installation
Currently the recommended way to install this package is as a development package using:

`pip install -e .`

and adding the `--user` option if not installing in a conda env. This lets changes made to the project automatically propagate to the install without the need to reinstall.

### Contributor
1. Create a fork of https://github.com/cta-chec/CHECRunPage to your GitHub 
account
2. `git clone https://github.com/YOURGITHUBACCOUNT/CHECRunPage.git`
3. `cd CHECRunPage`
4. `git remote add upstream https://github.com/cta-chec/CHECRunPage.git`
* To Update: 

```git fetch upstream && git checkout master &&  git merge upstream/master && git push origin master```


### Requirements

The listed requirements only apply to the server part. To use the submit client and the plugins assume to have a full `cta-conda` enviroment including the `Targetxxx` libs, `CHECLabPy`, `SSDAQ`,`SSM-analysis` etc.

## Usage

There is currently only one application in this project which is the `chec-runpage-submit`. Everytime it is invoked it instantiates both a a client and a server which makes development easier as changes in the server code will be in affect without the need of restarting a server. The help option `-h, --help` exposes all the options and arguments that are possible to use with the application. A typical example use would be:

```shell
chec-runpage-submit submit /path/to/run/files/* -u -p -g
```
which would generate statistics and plots for the supplied run files using the currently available plugins, update run stats from the google spreadsheet runlog (`-u`), generate `.rst` files for sphinx (`-p`) and generate the html (`-g`).  However to use the `-u` option and getting access to the spreadsheet a `googleapi` token is needed. 


### Token for the `googleapi`
To obtain a token for the `googleapi` either follow the steps exactly of this guide on a computer that has a browser: https://developers.google.com/sheets/api/quickstart/python and place the `token.pkl` file in the `data/` folder of this project. It should also be possible to first putting your `credentials.json` file (which you should have obtained from the previous link) and running: `chec-runpage-submit -u` which should open a browser were you have to validate your account and the token will be put in the correct folder automatically. 



## Writing your own run-page plugin

Your own run-page plugin has to inherit from `crundb.SubmitPluginBase` and the source file needs to be in the `crundb/modules` folder. 


```python
rom crundb import SubmitPluginBase
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
        ####################
        ###Process data#####
        ####################
        
        # make a database entry
        rpentry = {
                "modstats":{'run_timestamp':timestamp},# Here goes general stats that does not really belong in the 
                              # actual stats for this module and theses data 
                              # might be used by the server to make
                              # a run summary (needs to be configured in `pageconf.yaml)
                "modules": {#Here goes the data which makes up the entry in the run page
                        "figures": {# Figures
                            "ssamplitude_vs_time": savefig_to_buffer(fig),#we send the actual png and not the matplotlib figure
                            },
                        "title": "Slow Signal",# The heading to be used for this section
                        "stats":{"nframes": make_field('Number of good frames',nframes),
                                "rate":make_field('Frame rate',SVal(rate,'Hz'))}
                        },
                }
        #If you use matplotlib it is recomended that you close all the figures after saving them to buffer, 
        #otherwise they will stick in memory until the application terminates
        plt.close(fig)

        return rpentry            
```
For now the fields `modstats`,`modules`, `figures`, `title`, `stats` in the run page entry are required. For a complete simple example see `crundb/modules/slowsignal.py`. 
