import multiprocessing
import queue
import urllib.request
import time


def _download(url, queue):
    r = urllib.request.urlopen(url)
    while True:
        chunk = r.read(4096)
        queue.put(len(chunk) * 8)
        if not chunk:
            queue.put(None)
            break


def py_bandwidth_test(url, timeout):
    def download_stream():
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=_download, args=(url, q))
        p.start()
        deadline = time.time() + timeout
        while True:
            remaining_time = deadline - time.time()
            if remaining_time <= 0:
                break
            try:
                c = q.get(timeout=remaining_time)
                if c is None:
                    break
                yield c
            except queue.Empty:
                break
        p.terminate()

    start = time.time()
    received = sum(download_stream())
    duration = time.time() - start
    return {"bandwidth": received / duration}
