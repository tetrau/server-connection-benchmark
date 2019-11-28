import argparse
import json
import sys
import contextlib
import scb
import util
import render


def get_args():
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group('required arguments')
    required.add_argument("-o", "--output",
                          help="Output file path, use a single hyphen for "
                               "stdout.")
    parser.add_argument("-s", "--servers",
                        help="A JSON file contains the target servers. The JSON"
                             "file should contain a array of server objects. "
                             "A server object must have four fields. "
                             "\"vendor\": the vendor of the server, "
                             "\"location\": the location of the server, vendor"
                             "and location combined should be unique pair. "
                             "\"ping\": the host name of the server used for "
                             "ping test."
                             "\"download\": the download url (HTTP/HTTPSS) "
                             "for bandwidth test.")
    parser.add_argument("-r", "--resume-from",
                        help="Resume from the specify report file, in another "
                             "world, append this run's result to the old "
                             "report.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--render", required=False, action="store_true",
                       help="Render report data in json format to html file.")
    group.add_argument("--extract", required=False, action="store_true",
                       help="Extract report data from html file to json format.")
    group.add_argument("--peek", required=False, action="store_true",
                       help="Start a single test for each individual server "
                            "immediately, create a report and exit.")
    parser.add_argument("-i", "--input", required=False,
                        help="Set the input file path, use a single hyphen for "
                             "stdin. Used with --render and --extract")
    parser.add_argument("-e", "--every", type=int, default=30 * 60,
                        help="Set the minimal interval in seconds between two "
                             "benchmark batch, highly recommend use a divisor "
                             "of 24 hours (5min, 10min, 15min, 30min, 1h, 1.5h,"
                             " etc.)")
    parser.add_argument("-pc", "--ping-count", type=int, default=100,
                        help="How many ping packet should be send in one ping "
                             "test to a server.")
    parser.add_argument("--ping-chunk", type=int, default=8,
                        help="The maximum number of concurrent ping test.")
    parser.add_argument("-dt", "--download-timeout", type=int, default=45,
                        help="Specify a timeout in seconds for bandwidth test."
                             "If the download does not finished in timeout "
                             "seconds, it will be terminated and use what's"
                             "already received to calculate the bandwidth.")
    parser.add_argument("--json", required=False, action="store_true",
                        help="Change the report output format to JSON.")
    parser.add_argument("-v", "--version", required=False, action="store_true",
                        help="Show the version number")

    return parser, parser.parse_args()


def command_line_interface():
    def check_argument(name, message):
        a = getattr(arguments, name)
        if a is None:
            parser.error(message)
        else:
            return a

    @contextlib.contextmanager
    def open_io(filename, read=True):
        if filename == "-" and read:
            io = sys.stdin
        elif filename == "-" and not read:
            io = sys.stdout
        elif filename != "-" and read:
            io = open(filename)
        else:
            io = open(filename, "w+")
        try:
            yield io
        finally:
            if filename != "-":
                io.close()

    def get_argument_for_task():
        args = {}
        for n in ["ping_count", "ping_chunk", "download_timeout"]:
            args[n] = getattr(arguments, n)
        if arguments.json:
            args["render"] = render.json_render
        else:
            args["render"] = render.create_html_render()
        servers_file = check_argument("servers",
                                      "the following arguments are required: "
                                      "-s/--servers")
        with open_io(servers_file) as s:
            args["servers"] = json.load(s)
        if output == "-":
            args["record_file"] = sys.stdout
        else:
            args["record_file"] = output
        return args

    def get_resume_from():
        if arguments.resume_from:
            with open(arguments.resume_from) as f:
                if arguments.json:
                    return json.load(f)
                else:
                    return util.extract_from_html(f.read())
        else:
            return None

    parser, arguments = get_args()
    if arguments.version:
        print(scb.__version__)
        exit()
    output = check_argument("output", "the following arguments are required: "
                                      "-o/--output")
    if arguments.render:
        input = check_argument("input", "input (-i INPUT) argument "
                                        "must be set for --render-json option")
        with open_io(output, False) as o:
            with open_io(input) as i:
                o.write(render.create_html_render()(json.load(i)))
    elif arguments.extract:
        input = check_argument("input", "input (-i INPUT) argument "
                                        "must be set for --extract-html option")
        with open_io(output, False) as o:
            with open_io(input) as i:
                json.dump(util.extract_from_html(i.read()), o,
                          ensure_ascii=False, indent=2)
    elif arguments.peek:
        resume_from = get_resume_from()
        args = get_argument_for_task()
        args["resume_from"] = resume_from
        scb.test_and_record(**args)
    else:
        resume_from = get_resume_from()
        task = scb.create_task(**get_argument_for_task())
        every = check_argument("every",
                               " the following arguments are required:"
                               " -e/--every")
        scb.scheduler(task, every, resume_from)
