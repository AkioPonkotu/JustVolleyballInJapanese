Tcl 8.6.12 license fallback for Python distributions that omit tcl/tcl8.6/license.terms.
Source: https://github.com/tcltk/tcl/blob/core-8-6-12/license.terms

The release builder prefers the local runtime's license. If it is missing, it
requires a vendored license matching the exact Tcl patch version; it never
downloads licenses or dependencies on the end user's computer.
