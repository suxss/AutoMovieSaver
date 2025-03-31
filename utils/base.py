def singleton(cls):
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton

def get_file_ext(file_name: str):
    l = file_name.split(".")
    if len(l) > 1:
        return l[-1]
    return ""