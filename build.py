import os
import subprocess
import zipfile
import io
import stat

DIR = os.path.abspath(os.path.split(__file__)[0])
HTML_TEMPLATE_FILE = os.path.join(DIR, "dist", "template.html")
DIST_DIR = os.path.join(DIR, "dist")


def create_html_tempate():
    with open(os.path.join(DIR, "scb_js", "index.html")) as h:
        html = h.read()
    with open(os.path.join(DIR, "scb_js", "dist", "main.js")) as j:
        javascript = j.read()
    return html.replace("<script src=\"dist/main.js\"></script>",
                        "<script>{}</script>".format(javascript))


def build_html_template():
    subprocess.check_call(["npm", "run", "build"],
                          cwd=os.path.join(DIR, "scb_js"))
    with open(HTML_TEMPLATE_FILE, "w+") as o:
        o.write(create_html_tempate())


def rm(path):
    if os.path.isfile(path):
        os.remove(path)


def pack():
    target = os.path.join(DIST_DIR, "scb")
    buffer = io.BytesIO()
    src = os.path.join(DIR, "scb")
    rm(target)

    with zipfile.ZipFile(buffer, "w") as z:
        for py in [f for f in os.listdir(src) if f.endswith(".py")]:
            z.write(os.path.join(src, py), py)
        z.write(HTML_TEMPLATE_FILE, "template.html")
    with open(target, "wb+") as f:
        f.write("#!/usr/bin/env python3\n".encode(encoding="ascii"))
        buffer.seek(0)
        f.write(buffer.read())
    target_mode = os.stat(target).st_mode
    os.chmod(target, target_mode | stat.S_IEXEC)


def clean():
    rm(HTML_TEMPLATE_FILE)


def build():
    if not os.path.isdir(DIST_DIR):
        os.makedirs(DIST_DIR)
    build_html_template()
    pack()
    clean()


if __name__ == "__main__":
    build()
