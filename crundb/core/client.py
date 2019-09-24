import zmq
import zmq.asyncio

from crundb.core import submitplugin
from crundb import utils


class Client:
    def __init__(self, ip, port, zmqcontext=None, verbose=False):
        """Summary

        Args:
            ip (TYPE): Description
            port (TYPE): Description
            zmqcontext (None, optional): Description
        """
        self._context = zmqcontext or zmq.Context()
        self._sock = self._context.socket(zmq.REQ)
        con_str = "tcp://%s:%s" % (ip, port)
        if "0.0.0.0" == ip:
            self._sock.bind(con_str)
        else:
            self._sock.connect(con_str)
        self.verbose = verbose

    def pr(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def send_commands(self, command):
        self._sock.send_pyobj(command)
        print("waiting for response")
        rep = self._sock.recv_pyobj()
        return rep

    def update_from_runlog(self):
        command = [("update_from_runlog", "")]
        self._sock.send_pyobj(command)
        print("waiting for response")
        rep = self._sock.recv_pyobj()
        return rep

    def generate_pages(self, pages=None):
        command = [("generate_pages", pages)]
        self._sock.send_pyobj(command)
        print("waiting for response")
        rep = self._sock.recv_pyobj()
        return rep

    def list_submit_plugins(self):
        return [p.__name__ for p in submitplugin.SubmitPluginBase.subclasses]

    def submit(self, files: list, send=True, dry_run=False):
        run_collection = utils.classify_files(files)
        self.pr("Number of input files: {}".format(len(files)))
        self.pr("Files from {} runs ".format(len(run_collection.collection.keys())))
        self.pr("Type of files:")
        for key, count in run_collection.counters.items():
            self.pr(f"  `{key}`: {count}")
        if dry_run:
            return None
        plugins = []
        for p in submitplugin.SubmitPluginBase.subclasses:
            plugins.append(p())

        commands = []
        resps = []
        for run, run_files in run_collection.items():
            data = {"RUN": run, "modules": {}, "modstats": {}, "tags": set()}
            for p in plugins:
                try:
                    p_data = p.generate_submit(run_files)
                    data.update(p_data)
                    data["tags"].add(p.short_name)

                except Exception as e:
                    print(
                        f"An exception occured while plugin `{p.short_name}` was executing"
                    )
                    print(f"    `{e}`")

            if len(data["modules"].keys()) > 0:  # Dont send empty run stats
                command = ("submit", data)
                commands.append(command)
                if send:
                    self._sock.send_pyobj([command])
                    print("waiting for response")
                    resp = self._sock.recv_pyobj()
                    resps.append(resp)

        if send:
            return resps
        else:
            return commands


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run a slow signal simulation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("file", type=str, help="trigger pattern file")
    args = parser.parse_args()
    client = Client("127.0.0.101", port=7777)
    print(client.update_from_runlog())
    # print(client.submit(args.file))
    # print(client.generate_pages())
    print(client.send_command(("generate_html", "")))
