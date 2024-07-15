from std import exec_generator


def compare_element(v, _v):
    if isinstance(v, dict):
        if isinstance(_v, dict):
            yield from compare(v, _v)
        else:
            return 'type'

    elif isinstance(v, (list, tuple)):
        if isinstance(_v, (list, tuple)):
            yield from compare(v, _v)
        else:
            return 'type'

    else:
        try:
            b = v == _v
            if hasattr(b, 'all'):
                if b.all():
                    ...
                else:
                    return 'value'
            elif b:
                ...
            else:
                return 'value'
        except RuntimeError as e:
            return e


def compare(obj, _obj):

    if isinstance(obj, dict) and isinstance(_obj, dict):
        if len(obj) != len(_obj):
            print("keys lengths are not equal!")
            if len(obj) > len(_obj):
                print("missing keys in the right hand side:", obj.keys() - _obj.keys())
            else:
                print("missing keys in the left hand side:", _obj.keys() - obj.keys())

        for key, v in obj.items():
            if key not in _obj:
                print(f"{key} does not exist in the right hand side")
                continue
            keys = []
            if err_type := exec_generator(compare_element(v, _obj[key]), keys):
                print(f'{err_type} error, at key = {key}')
                yield key
            yield from keys

    elif isinstance(obj, (list, tuple)) and isinstance(_obj, (list, tuple)):
        if len(obj) != len(_obj):
            print("lengths are not equal!")
            print(len(obj), len(_obj))
            return

        for key, [v, _v] in enumerate(zip(obj, _obj)):
            keys = []
            if err := exec_generator(compare_element(v, _v), keys):
                print('index =', key, 'error info:', err)
                yield key
            yield from keys
