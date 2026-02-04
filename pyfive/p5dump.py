from pyfive import p5ncdump
import sys
import signal


def main(argv=None):
    """
    Provides some of the functionality of tools like ncdump and h5dump.
    By default this will attempt to do something similar to ncdump.
    - h will return this information
    - s will provide additional information, especially for chunked datasets.
    """
    if argv is None:
        argv = sys.argv[1:]  # ignore script name

    match argv:
        case []:
            raise ValueError("No filename provided")
        case ["-h"]:
            print(main.__doc__)
            return 0
        case [filename]:
            p5ncdump(filename, special=False)
            return 0
        case ["-s", filename]:
            p5ncdump(filename, special=True)
            return 0
        case _:
            raise ValueError(f"Invalid arguments: {argv}")


if __name__ == "__main__":
    # Set SIGPIPE to default behaviour on Unix (ignored safely on Windows)
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass

    try:
        sys.exit(main())
    except BrokenPipeError:
        # Happens if pipe is closed early (e.g. `| head` or user quits `more`)
        try:
            sys.stderr.flush()
        except Exception:
            pass
        sys.exit(0)
    except Exception as e:
        # Any other error: no traceback, just a clean message
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
