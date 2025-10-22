from pyfive import p5ncdump
import sys

def main(argv=None):
    """
    Provides some of the functionality of tools like ncdump and h5dump.
    By default this will attempt to do something similar to ncdump.
    - h will return this information
    - s (not yet implemented) will provide additional information
    """
    if argv is None:
        argv = sys.argv[1:]  # ignore script name

    match argv:
        # script      → error (no filename)
        case []:
            raise ValueError("No filename provided")

        # script -h   → help
        case ["-h"]:
            print(main.__doc__)
            return 0

        # script filename
        case [filename]:
            p5ncdump(filename, special=False)
            return 0

        # script -s filename
        case ["-s", filename]:
            p5ncdump(filename, special=True)
            return 0

        # Anything else → error
        case _:
            raise ValueError(f"Invalid arguments: {argv}")

if __name__ == '__main__':
    sys.exit(main())
