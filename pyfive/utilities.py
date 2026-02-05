"""Utility interceptor."""

import inspect
import io
import logging


class Interceptor:
    """Intercepts file-io and logs what is going on.

    Used in debugging file reading issues and optimisation.
    """

    def __init__(self, fh, activated=True):
        self._fh = fh
        self.activated = activated

    def seek(self, offset, whence=0):
        """Seek."""
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
        """Read."""
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

class MetadataBufferingWrapper:
    """
    Wraps a file-like object to eagerly buffer metadata from S3 or remote sources.

    On first use, reads a large chunk of data into memory. Subsequent reads
    hit the buffer first, reducing network calls for scattered metadata reads.
    """

    def __init__(self, fh, buffer_size: int = 1):
        """
        Initialize wrapper.

        Parameters
        ----------
        fh : file-like
            Original file handle (S3File or similar)
        buffer_size : int
            Size of metadata buffer to read upfront (MB, default=1MB)
        """
        MB = 2**20
        self.fh = fh
        self.buffer_size = buffer_size*MB
        self.buffer = None
        self.buffer_start = 0
        self.position = 0
        self._is_closed = False

    @property
    def closed(self) -> bool:
        """Return whether file is closed."""
        return self._is_closed

    def _ensure_buffer(self):
        """Eagerly read metadata buffer on first access."""
        if self.buffer is None:
            self.fh.seek(0)
            data = self.fh.read(self.buffer_size)
            self.buffer = io.BytesIO(data)
            self.buffer_start = 0
            logging.info(
                '[pyfive] Eagerly buffered %d bytes of metadata from remote file',
                len(data)
            )

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seek to position."""
        if whence == 0:  # SEEK_SET
            self.position = offset
        elif whence == 1:  # SEEK_CUR
            self.position += offset
        elif whence == 2:  # SEEK_END
            # For remote files, we might not know the end
            self.fh.seek(offset, whence)
            self.position = self.fh.tell()
        return self.position

    def read(self, size: int = -1) -> bytes:
        """Read from buffer or fall through to original fh."""
        self._ensure_buffer()

        # Calculate buffer bounds
        buffer_end = self.buffer_start + self.buffer.getbuffer().nbytes

        # If read is within buffer, serve from buffer
        if self.position >= self.buffer_start and self.position < buffer_end:
            # Position within buffer
            offset_in_buffer = self.position - self.buffer_start
            self.buffer.seek(offset_in_buffer)

            if size == -1:
                data = self.buffer.read()
            else:
                data = self.buffer.read(size)

            self.position += len(data)

            # If we didn't read enough and are at buffer end, fall through to fh
            if size != -1 and len(data) < size and self.position >= buffer_end:
                self.fh.seek(self.position)
                additional = self.fh.read(size - len(data))
                data += additional
                self.position += len(additional)

            return data
        else:
            # Read is beyond buffer or before buffer, use original fh
            self.fh.seek(self.position)
            data = self.fh.read(size)
            self.position += len(data)
            return data

    def tell(self) -> int:
        """Return current position."""
        return self.position

    def close(self):
        """Close underlying file."""
        self._is_closed = True
        if self.buffer is not None:
            self.buffer.close()
        self.fh.close()