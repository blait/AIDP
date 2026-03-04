_progress_callback = None


def set_progress_callback(cb):
    global _progress_callback
    _progress_callback = cb


def notify(msg):
    print(msg, flush=True)
    if _progress_callback:
        _progress_callback(msg)
