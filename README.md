## Common problems

```
ImportError: cannot import name '_message' from 'google.protobuf.pyext' (.../venv/lib/python3.7/site-packages/google/protobuf/pyext/__init__.py)
```

Reinstall `protobuf`:

```
pip3 install --upgrade --force-reinstall protobuf
```
