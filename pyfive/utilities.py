import inspect

class Interceptor:
    """
    Intercepts file-io and logs what is going on.
    Used in debugging file reading issues and optimisation.
    """
    def __init__(self, fh, activated=True):
        self._fh = fh
        self.activated=activated
    def seek(self, offset, whence=0):
        if self.activated:
            caller = inspect.currentframe().f_back
            if caller is not None:
                func = caller.f_code.co_name
                fname = caller.f_code.co_filename
                lineno = caller.f_lineno
            else:
                func, fname, lineno = "<module>", "<unknown>", 0
            print(f"seek: {offset}, {whence} (called from {func})")
        return self._fh.seek(offset, whence)    
    def read(self, size=-1):
        if self.activated:
            caller = inspect.currentframe().f_back
            if caller is not None:
                func = caller.f_code.co_name
                fname = caller.f_code.co_filename
                lineno = caller.f_lineno
            else:
                func, fname, lineno = "<module>", "<unknown>", 0
            pos = self._fh.tell()
            print(f"read: {size} bytes at {pos} (called from {func})")
        return self._fh.read(size)