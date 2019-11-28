import json
import os
import util


def get_template():
    program_dir = os.path.abspath(os.path.split(__file__)[0])
    if os.path.isfile(program_dir):
        return util.read_zip(program_dir, "template.html")
    else:
        with open(os.path.join(program_dir, "template.html")) as t:
            return t.read()


def create_html_render(template=None):
    if template is None:
        template = get_template()

    def render(report):
        report_in_js = json.dumps(report)
        data_def_template = (
            "var data = \n"
            "//---- BEGIN DATA ----//\n"
            "{}\n"
            "//---- END DATA ----//")
        return template.replace("//INJECT_DATA_HERE//",
                                data_def_template.format(report_in_js))

    return render


def json_render(report):
    return json.dumps(report, ensure_ascii=False, indent=2)
