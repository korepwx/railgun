```python
def reform_path(path):
    path = path.replace('\\', '/')
    lead_slash = path.startswith('/')
    ret = []

    for p in path.split('/'):
        # skip continous slashes, or single '.'
        if (p == '.' or not p):
            continue
        # remove parent dir if p is '..'
        if (p == '..'):
            if (not ret):
                raise ValueError('.. out of root')
            ret.pop()
        # otherwise add the simple part into ret
        else:
            ret.append(p)

    ret = '/'.join(ret)
    if (lead_slash):
        ret = '/' + ret
    return ret
```
