# Source provenance and historical reference

FRESH has a Python implementation and a browser implementation in `web/`.
Both are compared with a preserved earlier TypeScript implementation.

## Preserved reference

The files in `original_fresh/` come from
[commit a062357](https://github.com/paohenr1/Fresh/tree/a0623571bd85c0c75c284efe4ba4dee550db8d9b).
[SOURCE.json](../SOURCE.json) records the full commit identifier and SHA-256
hashes of the reference calculation, tests, interface and documentation files.
The reference is kept unchanged so comparisons remain reproducible.

**The archived README and specification describe that historical version.**
Their development instructions, environment assumptions and defaults are not
instructions for the current application. Use the [current usage guide](usage.md)
and [browser development guide](../web/README.md) instead.

The earlier main application is also available at
[commit b3368e7](https://github.com/paohenr1/Fresh/tree/b3368e7843ae9661916cc2ba4ce7f8cde125f300).
Neither historical version is the deployed browser application.

## Differences from the reference

The current implementations add independent numeric contribution-indexation
rates, optional pension indexation and saving of net retirement-income surplus
to Cash. The [model comparison](../MODEL_REVIEW.md) explains these differences
and the baseline assumptions they retain.

The original-source comparison harness uses an in-memory extension for cases
that require numeric contribution rates or surplus saving; it does not edit
the preserved files. Agreement with that extended reference is distinguished
from agreement with the original unchanged model. See
[verification](../VERIFICATION.md) for commands, coverage and limitations.

## Historical records

[Historical verification](verification-history.md) records earlier test results
and interface changes. Dates and report layouts in those records belong to the
versions tested; they are not results from a new run or a specification for the
current interface.

[Back to the README](../README.md).
