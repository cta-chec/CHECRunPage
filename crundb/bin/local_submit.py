import argparse
from crundb.core.client import Client
from crundb.core.server import Server
from multiprocessing import Process


def serverprocess(port):
    server = Server(ip="127.0.0.101", port=7777)
    server.run()


def run_local():

    parser = argparse.ArgumentParser(
        description="Running the client and server locally",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "cmd",
        nargs="?",
        type=str,
        help="trigger pattern file",
        choices=["submit", "cmd", "ls"],
    )

    parser.add_argument("args", type=str, nargs="*", help="trigger pattern file")

    parser.add_argument(
        "-u,--update-runlog",
        dest="update",
        action="store_true",
        help="update from runlong",
    )
    parser.add_argument(
        "-p,--generate-rst-pages",
        dest="rst",
        action="store_true",
        help="generate rst pages",
    )

    parser.add_argument(
        "-g,--generate-html-pages",
        dest="html",
        action="store_true",
        help="generate html pages",
    )
    parser.add_argument(
        "-v,--verbose", dest="verbose", action="store_true", help="Verbose mode"
    )

    parser.add_argument(
        "-d,--dry-run",
        dest="dry_run",
        action="store_true",
        help="Dry run (applies only submit)",
    )
    parser.add_argument

    args = parser.parse_args()
    # print(args)
    client = Client("127.0.0.101", port=7777, verbose=args.verbose)
    if args.cmd == "ls":
        print(client.list_submit_plugins())
        exit()

    p = Process(target=serverprocess, args=(7777,))
    p.start()

    commands = []
    if args.update:
        commands.append(("update_from_runlog", ""))

    if args.cmd == "submit":
        client.submit(args.args, True, args.dry_run)
    if args.rst:

        commands.append(("generate_pages", None))
    if args.cmd == "cmd":
        print("not implemented yet")
        p.terminate()
        exit()
    if args.html:
        commands.append(("generate_html", ""))
    client.send_commands(commands)

    p.terminate()


if __name__ == "__main__":
    run_local()
