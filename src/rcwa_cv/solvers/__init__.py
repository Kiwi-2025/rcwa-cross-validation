from importlib import import_module


MODULES = {
    "meent": "meent_cpu", "torcwa": "torcwa_cuda", "grcwa": "grcwa_cpu",
    "lumerical": "lumerical",
}


def adapter(name):
    return import_module(f".{MODULES[name]}", __package__)
