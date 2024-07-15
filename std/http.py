import json
import requests
from json.decoder import JSONDecodeError

def json_post(url, data, headers={}):
    try:
        headers['Content-Type'] = "application/json"
        text = requests.post(
            url,
            data=json.dumps(data, ensure_ascii=False).encode(encoding='utf-8'),
            headers=headers).text
        try:
            return json.loads(text)
        except JSONDecodeError:
            return text
    except Exception as e:
        return e


def json_post_curl(url, data):
    data = json.dumps(data, ensure_ascii=False)#.encode(encoding='utf-8')
    return f"curl -H 'Content-Type: application/json' -X POST '{url}' -d'{data}'"
    
def get(url, **kwargs):
    import regex as re
    if kwargs:
        url += "?"
        parameters = []
        for key, value in kwargs.items():
            if isinstance(value, str):
                value = re.sub(r'\+', '%2B', value)

            parameters.append(f"{key}={value}")
        url += '&'.join(parameters)

    text = requests.get(url).text
    try:
        return json.loads(text)
    except JSONDecodeError:
        return text
    
def form_post(url, data):
    for key, value in data.items():
        if not isinstance(value, str):
            data[key] = json.dumps(value, ensure_ascii=False)
            
    text = requests.post(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}).text
    try:
        return json.loads(text)
    except JSONDecodeError:
        return text


def octet_stream_post(url, filename, data):
    text = requests.post(
        url,
        data=data,
        headers={"Content-Type": "application/octet-stream", 'filename': filename, 'Content-Length': str(len(data))}).text
    try:
        return json.loads(text)
    except JSONDecodeError:
        return text

def getParameters(request):
    #from flask.globals import request
    return {**request.args} | {**request.form} or {**request.json}