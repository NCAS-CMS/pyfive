"""Generates sidebar/toctree.

Generates the common sidebar/toctree for the sphinx/ReadTheDocs
documentation of the Pyfive and its subprojects.
"""

import os


def _write_if_changed(fname, contents):
    """Write/update file only if changed."""
    try:
        with open(fname, "r") as stream:
            old_contents = stream.read()
    except IOError:
        old_contents = ""

    if old_contents != contents:
        with open(fname, "w") as stream:
            stream.write(contents)


def generate_sidebar(conf, conf_api):
    """Generate sidebar.

    Generate sidebar for ReadTheDocs with links to subprojects and
    superprojects accordingly.
    """
    # determine 'latest' or 'stable'
    # if not conf.do_gen:
    do_gen = os.environ.get("SIDEBAR", None) == "1" or conf["on_rtd"]

    lines = ["", ".. DO NOT MODIFY! THIS PAGE IS AUTOGENERATED!", ""]

    def _toctree():
        lines.extend([".. toctree::", "   :maxdepth: 1", ""])

    def _endl():
        lines.append("")

    def _write(project, desc, link, mapping=conf['intersphinx_mapping']):
        if project != conf_api:
            if do_gen:
                args = desc, mapping[project][0], link
                lines.append("    %s <%s%s.html>" % args)
        else:
            args = desc, link
            lines.append("    %s <%s>" % args)

    def _header(project, text):
        if project == conf_api or do_gen:
            lines.extend([".. toctree::", "   :maxdepth: 2"])
            lines.extend(["   :caption: %s" % text, ""])

    #
    # Specify the sidebar contents here
    #

    _header("pyfive", "Pyfive")
    _write("pyfive", "Introduction", "introduction")
    _write("pyfive", "Getting started", "quickstart/index")
    # _write("pyfive", "Examples", "examples")
    # _write("pyfive", "Contributing to the community", "community/index")
    # _write("pyfive", "Utilities", "utils")
    # _write("pyfive", "API Reference", "api/pyfive")
    # _write("pyfive", "Frequently Asked Questions", "faq")
    # _write("pyfive", "Changelog", "changelog")
    _endl()

    _write_if_changed("_sidebar.rst.inc", "\n".join(lines))
