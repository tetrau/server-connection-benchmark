import zipfile
import json


def read_zip(zip_file, file_in_zip):
    with zipfile.ZipFile(zip_file) as z:
        with z.open(file_in_zip) as f:
            return f.read().decode()


def extract_from_html(html):
    json_str = html.split("//---- BEGIN DATA ----//")[-1]
    json_str = json_str.split("//---- END DATA ----//")[0]
    return json.loads(json_str)
