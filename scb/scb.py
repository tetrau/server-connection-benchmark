import subprocess
import re
import time
import functools
import datetime
import shutil
import platform
import downloader

__version__ = "0.0.1"


def ping_test(host, count):
    is_windows = platform.system() == "Windows"
    cmd = ["ping", "-n", str(count), host] \
        if is_windows else ["ping", "-q", "-c", str(count), host]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    return p


def parse_ping_test_result(p):
    is_windows = platform.system() == "Windows"
    tx_rx_pattern = "Packets: Sent = (\d+), Received = (\d+)," if is_windows \
        else "(\d+) .*transmitted, (\d+) .*received"
    latency_pattern = "Minimum = \d+ms, Maximum = \d+ms, Average = (\d+)ms" \
        if is_windows else "min/avg/max/.+ = [\d.]+/[\d.]+/([\d.]+)/[\d.]+ ms"

    r = p.stdout.read().decode()
    try:
        transmitted_received = re.findall(tx_rx_pattern, r)
        transmitted, received = transmitted_received[0]
        latency = re.findall(latency_pattern, r)
        latency = latency[0]
    except IndexError:
        raise ValueError("Unsupported ping output:\n{}".format(r))
    packet_loss = 1 - (int(received) / int(transmitted))
    return {"latency": float(latency), "packetLoss": packet_loss}


def join_popen(ps):
    ps = list(ps)
    while True:
        if any(map(lambda p: p.poll() is None, ps)):
            time.sleep(0.1)
        else:
            break
    return ps


def bandwidth_test(url, timeout):
    if shutil.which("curl") is None:
        return downloader.py_bandwidth_test(url, timeout)

    start = time.time()
    p = subprocess.Popen(["curl", url],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL
                         )
    try:
        outs, errs = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        outs, errs = p.communicate()
    end = time.time()
    return {"bandwidth": (8 * len(outs)) / (end - start)}


def server_name(s):
    return "{}: {}".format(s["vendor"], s["location"])


def test_ping_all(servers, ping_count, ping_chunk):
    ping_result = []
    ping_test_ = functools.partial(ping_test, count=ping_count)
    print("Start ping test:")
    for i in range(0, len(servers), ping_chunk):
        server_chunk = servers[i:i + ping_chunk]
        target = [s["ping"] for s in server_chunk]
        rs = list(map(parse_ping_test_result,
                      join_popen(
                          map(ping_test_,
                              target))))
        ping_result.extend(rs)
        for s, r in zip(server_chunk, rs):
            print(server_name(s),
                  "latency: [{:.0f} ms] packetLoss: [{:.0f}%]".format(
                      r["latency"], r["packetLoss"] * 100))
    return ping_result


def format_bandwidth(b):
    if b < 1024:
        return "{:.2f} bps".format(b)
    elif b < 1024 * 1024:
        return "{:.2f} kbps".format(b / 1024)
    else:
        return "{:.2f} mbps".format(b / (1024 * 1024))


def test_bandwidth_all(servers, timeout):
    bandwidth_result = []
    for s in servers:
        print("Start bandwidth test for", server_name(s), end="", flush=True)
        r = bandwidth_test(s["download"], timeout)
        bandwidth_result.append(r)
        print(" [{}]".format(format_bandwidth(r["bandwidth"])))
    return bandwidth_result


def test_all(servers, ping_count, ping_chunk, dwonload_timeout):
    ping_result = test_ping_all(servers, ping_count, ping_chunk)
    bandwidth_result = test_bandwidth_all(servers, dwonload_timeout)
    result = []
    for s, p, b in zip(servers, ping_result, bandwidth_result):
        result.append({"vendor": s["vendor"],
                       "location": s["location"],
                       "bandwidth": b["bandwidth"],
                       "latency": p["latency"],
                       "packetLoss": p["packetLoss"]})
    return result


def scheduler(task, every, init=None):
    first_batch = (time.time() // every + 1) * every
    first_batch_datetime = datetime.datetime.fromtimestamp(first_batch)
    print("Start benchmark, the first batch has been scheduled at {}"
          .format(first_batch_datetime.isoformat()))
    s = init
    while True:
        time.sleep(every - (time.time() % every))
        print("Start test batch:", datetime.datetime.now().isoformat())
        s = task(s)
        print("Finish test batch at", datetime.datetime.now().isoformat())


def test_and_record(servers, record_file, render, ping_count, ping_chunk,
                    download_timeout, resume_from=None):
    if resume_from is None:
        record = []
    else:
        record = resume_from
    time_now = time.time()
    result = test_all(servers, ping_count=ping_count, ping_chunk=ping_chunk,
                      dwonload_timeout=download_timeout)
    record.append({"time": time_now, "result": result})
    if hasattr(record_file, "write"):
        record_file.write(render(record))
    else:
        with open(record_file, "w+") as f:
            f.write(render(record))
    return record


def create_task(servers, record_file, render,
                ping_count, ping_chunk, download_timeout):
    def task(r):
        return test_and_record(servers=servers, record_file=record_file,
                               render=render, ping_count=ping_count,
                               ping_chunk=ping_chunk,
                               download_timeout=download_timeout, resume_from=r)

    return task
