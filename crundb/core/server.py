import crundb
from crundb.utils import Daemon
from crundb.modules import qchecrunlog
from crundb.utils import (
    printNiceTimeDelta,
    nested_access,
    update_nested_dict,
    dnest,
    make_field,
    nestd_key_exist
)
from crundb import utils
from crundb.core import sphinx
from crundb.core import parse

import asyncio
import logging
import inspect
import os
import zmq
import zmq.asyncio
from collections import defaultdict
import datetime
import subprocess
import pickle
from jinja2 import Environment, FileSystemLoader
import yaml


logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def create_runplot_folder(folder: str) -> str:
    """Summary

    Args:
        folder (str): Description

    Returns:
        str: Description
    """
    path = os.path.join(
        os.path.dirname(os.path.dirname(crundb.__file__)),
        "dbdisplay",
        "source",
        "_static",
        folder,
    )
    try:
        os.mkdir(path)
        return path
    except OSError:
        # print ("Creation of the directory %s failed" % path)
        return path
    else:
        print("Successfully created the directory %s" % path)


class RecieverDaemonWrapper(Daemon):
    def __init__(
        self,
        server_cls,
        stdout="/dev/null",
        stderr="/dev/null",
        set_taskset=False,
        core_id=0,
        log_level="INFO",
        **kwargs,
    ):
        # Deamonizing the server
        Daemon.__init__(
            self,
            "/tmp/{}_daemon.pid".format(server_cls.__name__),
            stdout=stdout,
            stderr=stderr,
        )
        self.server_cls = server_cls
        self.kwargs = kwargs
        self.set_taskset = set_taskset
        self.core_id = str(core_id)

    def run(self):

        self.server = self.server_cls(**self.kwargs)
        self.server.run()


class Server:
    def __init__(self, ip, port):
        self.loop = asyncio.get_event_loop()
        self.log = log
        self.recv_addr = (ip, port)
        self.corrs = []
        # setting up communications socket
        self._context = zmq.asyncio.Context()
        self._com_sock = self._context.socket(zmq.REP)
        self._com_sock.bind("tcp://{}:{}".format(*self.recv_addr))
        self.log.info('Socket bind at "tcp://{}:{}"'.format(*self.recv_addr))
        self.path = os.path.dirname(os.path.dirname(crundb.__file__))
        self.display_path = utils.get_dbdisplay_folder()#os.path.join(self.path, "dbdisplay")
        self.run_data_path = os.path.join(self.display_path, "db")
        needed_folders = [self.run_data_path,
                            os.path.join(self.display_path, "build"),
                            os.path.join(utils.get_source_folder(),'_static'),
                            os.path.join(utils.get_source_folder(),'_templates'),
                            os.path.join(utils.get_source_folder(),'runs')]
        for nf in needed_folders:
            utils.create_dir(nf)

        self.lib_path = os.path.join(self.path, "crundb")
        self.template_dir = os.path.join(utils.get_data_folder(), "templates")
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        if not os.path.exists(os.path.join(self.display_path, "db", "rundb.pkl")):
            with open(
                os.path.join(self.display_path, "db", "rundb.pkl"), "wb"
            ) as rundbfile:
                pickle.dump(defaultdict(set), rundbfile)

    def run(self):
        """ Starts the eventloop of the ReceiverServer (blocking)
        """

        self.log.info("Starting server")
        self._introspect()
        for c in self.corrs:
            self.loop.create_task(c)

        try:
            self.loop.run_forever()
        except Exception as e:
            self.log.error("Exception caught while running event loop: {}".format(e))
            print("Exception caught while running event loop: {}".format(e))
        self.loop.close()

    def _introspect(self):
        # Introspecting to find all methods that
        # handle commands
        method_list = inspect.getmembers(self, predicate=inspect.ismethod)
        self.cmds = {}
        for method in method_list:
            if method[0][:4] == "cmd_":
                self.cmds[method[0][4:]] = method[1]
            if method[0][:3] == "ct_":
                self.corrs.append(method[1]())

    async def ct_handle_commands(self):
        """
        This is the server command that handles
        incomming control commands
        """
        while True:
            message = await self._com_sock.recv_pyobj()
            # print(message)
            self.log.info("Handling incoming %d commands " % len(message))
            print("Handling incoming %d commands " % len(message))
            reply = []
            for command in message:
                self.log.info("Handling command %s " % command[0])
                cmd = command[0]

                if cmd in self.cmds.keys():
                    reply.append(self.cmds[cmd](command[1]))
                else:
                    reply.append("Error, No command `%s` found." % (cmd))
                    self.log.info("Incomming command `%s` not recognized" % (cmd))
            print("reply", reply)
            self._com_sock.send_pyobj(reply)

    def cmd_submit(self, data):
        """Summary

        Args:
            data (TYPE): Description

        Returns:
            TYPE: Description
        """
        print("submitting")
        with open(
            os.path.join(self.display_path, "db", "rundb.pkl"), "rb"
        ) as rundbfile:
            rundb = pickle.load(rundbfile)
        runnumber = data["RUN"]
        rundb[runnumber].update(data["tags"])

        with open(
            os.path.join(self.display_path, "db", "rundb.pkl"), "wb"
        ) as rundbfile:
            pickle.dump(rundb, rundbfile)
        runfilename = os.path.join(self.run_data_path, "{}.pkl".format(runnumber))

        if os.path.exists(runfilename):
            with open(runfilename, "rb") as f:
                runobject = pickle.load(f)
        else:
            runobject = {
                "RUN": "{}".format(runnumber),
                "modstats": defaultdict(dict),
                "modules": defaultdict(dict),
            }

        runobject["modules"].update(data["modules"])
        if "modstats" in runobject:
            runobject["modstats"].update(data["modstats"])
        else:
            runobject["modstats"] = data["modstats"]
        with open(runfilename, "wb") as f:
            runobject = pickle.dump(runobject, f)

        return "success"

    def update_from_runlog(self):
        """Summary

        Returns:
            TYPE: Description
        """
        print("Updating runs from runlog...")
        runs = qchecrunlog.query_chec_runlog()
        try:
            with open(
                os.path.join(self.display_path, "db", "rundb.pkl"), "rb"
            ) as rundbfile:
                rundb = pickle.load(rundbfile)
        except:
            rundb = defaultdict(set)
        for runnumber, run in runs.items():
            if not runnumber.isdigit():
                continue
            runfilename = os.path.join(
                self.run_data_path, "Run{}.pkl".format(runnumber)
            )
            tags = rundb["Run{}".format(runnumber)]
            tags.add("logged")
            if len(run["Run Type"]) > 1:
                tags.add(run["Run Type"])
            if "Object" in run and len(run["Object"]) > 0:
                tags.add(run["Object"])
            if os.path.exists(runfilename):
                with open(runfilename, "rb") as f:
                    runobject = pickle.load(f)
            else:
                runobject = {
                    "RUN": "Run{}".format(runnumber),
                    "modules": defaultdict(dict),
                }
            runlog_mod = {"stats": run, "title": "Run log"}

            runobject["modules"]["runlog"].update(runlog_mod)
            with open(runfilename, "wb") as f:
                runobject = pickle.dump(runobject, f)
        with open(
            os.path.join(self.display_path, "db", "rundb.pkl"), "wb"
        ) as rundbfile:
            pickle.dump(rundb, rundbfile)

        return "success"

    def cmd_update_from_runlog(self, args):
        return self.update_from_runlog()

    def cmd_generate_pages(self, args):
        """Summary

        Args:
            args (TYPE): Description
        """
        print("Generating run pages...")
        self.n_pages_generated = 0
        self.n_runs_processed = 0
        self.tmp_runlist = defaultdict(set)
        if os.path.exists(os.path.join(self.display_path, "db", "rundb.pkl")):
            with open(
                os.path.join(self.display_path, "db", "rundb.pkl"), "rb"
            ) as rundbfile:
                rundb = pickle.load(rundbfile)
        else:
            print("RST pages could not be generated as no rundb file was found")
            return

        with open(os.path.join(utils.get_data_folder(), "pageconf.yaml")) as f:
            self.page_config = yaml.load(f,Loader=yaml.SafeLoader)
        args = args or list(rundb.keys())



        page_data = {}

        for run in args:
            runfilename = os.path.join(self.run_data_path, "{}.pkl".format(run))
            if os.path.exists(runfilename):
                with open(runfilename, "rb") as f:
                    runobject = pickle.load(f)
                if len(runobject["modules"]) == 0:
                    continue
                data = self.generate_runpage(runobject,rundb)
                page_data[data["RUN"]] = data
                self.n_runs_processed += 1
### SEPARATE PLUGIN ###
                # should be put in separate plugin
                # pconf = dnest(self.page_config,"RunSummary.sourceoptions")# self.page_config["RunSummary"]["sourceoptions"]
                tstr = data["stats"]["run_length"]
                if len(tstr) > 3:
                    t = datetime.datetime.strptime(tstr, "%H:%M:%S")
                    delta = datetime.timedelta(
                        hours=t.hour, minutes=t.minute, seconds=t.second
                    )
                    if delta.seconds < 120:
                        self.tmp_runlist[data["RUN"]].add("short")
### END SEPARATE PLUGIN ###
            else:
                self.log.error("No run found named {}".format(run))

        self.generate_indexpage(page_data,rundb)
        print("Number of pages generated {}".format(self.n_pages_generated))
        print("Number of processed runs {}".format(self.n_runs_processed))
    def cmd_generate_html(self, args):
        """Summary

        Args:
            args (TYPE): Description

        Returns:
            TYPE: Description
        """
        print("Generating html pages...")
        subprocess.run(["make", "clean"], cwd=self.display_path)
        ret = subprocess.run(["make", "html"], cwd=self.display_path)

        return ret, ret.stderr

    def generate_runpage(self, data, rundb):
        """Summary

        Args:
            data (TYPE): Description

        Returns:
            TYPE: Description
        """
        runnumber = data["RUN"]
        runfolder = create_runplot_folder(runnumber)

        for module in data["modules"].keys():
            if "stats" in data["modules"][module]:
                for name, field in data["modules"][module]["stats"].items():
                    if not isinstance(field, dict):
                        data["modules"][module]["stats"][name] = {
                            "label": name,
                            "val": field,
                        }
                        field = data["modules"][module]["stats"][name]
### SEPARATE PLUGIN ###
                    if field["val"] == "-":
                        field["val"] = "--"
### END SEPARATE PLUGIN ###
            # extracting figures and writing them to file from the pickles
            if "figures" in data["modules"][module]:
                figsnames = []
                for name, fig in data["modules"][module]["figures"].items():
                    with open(os.path.join(runfolder, name + ".png"), "wb") as f:
                        f.write(fig)
                    figsnames.append(
                        os.path.join("..", "_static", runnumber, name + ".png")
                    )
                data["modules"][module]["figures"] = figsnames

        data["tags"] = rundb[runnumber]

        # populating the root stats field:
        sourceopts = dnest(self.page_config, "RunPage.RunSummary")
        stats = {}
        for fieldkey, opts in sourceopts.items():
            for opt in opts["sources"]:
                dict_path = opt.split(".")
                if len(dict_path) > 1 and dict_path[1] not in data["modules"]:
                    continue
                stats[fieldkey] = make_field(opts["label"], dnest(data, opt) or "--")
                break
            else:
                stats[fieldkey] = make_field(opts["label"], "--")

        data["stats"] = stats

        def apply_formatting(data,keys,cond,func):
            if nestd_key_exist(data,keys):
                d = {}
                exec("c = "+cond,globals(),d)
                exec("f = "+func,globals(),d)
                update_nested_dict(data,keys,d['c'],d['f'])
        for i,form in enumerate(dnest(self.page_config, "RunPage.Formating")):
            if form['func'] == "apply_formatting":
                try:
                    apply_formatting(data,**form["args"])
                except Exception as e:
                    print("An exception occured during formatting nr {}: {}".format(i,e))

        runpagetemplate = self.env.get_template("runpagetemplate.j2")

        runpage = runpagetemplate.render(data=data, diag=data["modules"])

        runpagefile = open(
            os.path.join(self.display_path, "source", "runs", runnumber + ".rst"), "w"
        )
        runpagefile.writelines(runpage)
        self.n_pages_generated +=1
        return data

    def generate_indexpage(self, page_data,rundb):

        indextemplate = self.env.get_template("run_index_template.j2")
        runtags = defaultdict(list)
        for run, tags in sorted(rundb.items()):
            tmp_tags = self.tmp_runlist[run]
            for tag in list(tags) + list(tmp_tags):
                runtags[tag].append(run)


        indexes = self.page_config["Indexes"]["pages"]

        # Generating index pages for different selections
        main_toc = []
        for index, conf in indexes.items():
            main_toc.append(index)
            self.run_sel_page(index, conf, page_data, indextemplate, runtags)

        # Generating main page
        toc = sphinx.toc(main_toc, maxdepth=1)
        main_pagetemplate = self.env.get_template("main_page.j2")
        main_page = main_pagetemplate.render(indextoc=toc)

        indexpagefile = open(
            os.path.join(self.display_path, "source", "index.rst"), "w"
        )
        indexpagefile.writelines(main_page)
        print(runtags.keys())
        self.n_pages_generated +=1


    def run_sel_page(self, index, conf, page_data, indextemplate, runtags):

        table = []
        # defining columns for the table
        cols = ["Run"] + [field["label"] for k, field in conf["fields"].items()]
        toc_path = []
        #evaluate tag selection expression in configuration
        sel_runs = parse.eval_tag_expr(expr=conf['tags_sel'],retr_val=runtags)


        # Create run list page
        for run in sorted(sel_runs):
            toc_path.append("runs/" + run)
            row = {"Run": ":ref:`{}`".format(run)}
            for field, settings in conf["fields"].items():
                row[settings["label"]] = str(
                    nested_access(page_data[run], *(settings["sources"][0].split(".")))
                )
            table.append(row)

        table_rendered = sphinx.simple_tbl(table, cols)
        toc_rendered = sphinx.toc(toc_path, hidden="")
        indexpage = indextemplate.render(
            title=conf["title"],
            tables={conf["title"]: {"table": table_rendered, "toc": toc_rendered}},
        )
        with open(os.path.join(self.display_path, "source", f"{index}.rst"), "w") as f:
            f.writelines(indexpage)
        self.n_pages_generated +=1



if __name__ == "__main__":
    server = Server(ip="127.0.0.101", port=7777)
    server.run()
