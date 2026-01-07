# Bug Report: Extraneous Blank Line in `make help` Output

**File:** `Makefile`

**Line:** 214

**Description:**
The `help` target in the `Makefile` uses an `awk` command to generate a formatted list of available targets. The `BEGIN` block of this `awk` script contains a `printf` statement that prints a color-formatted, empty line to the console.

```awk
'BEGIN {FS = ":.*##"; printf "\033[36m\033[0m\n"} ...'
```

This results in an unnecessary and visually disruptive blank line appearing at the top of the "Available targets:" list every time `make help` is run.

**Impact:**
This is a minor formatting bug that affects the usability and polish of the command-line interface provided by the `Makefile`. It does not affect any functional parts of the build or application stack.

**Proposed Fix:**
The fix is to remove the extraneous `printf "\033[36m\033[0m\n"` statement from the `BEGIN` block. The corrected `awk` command will be:

```awk
'BEGIN {FS = ":.*##"} ...'
```

This change is minimal, targeted, and will resolve the formatting issue without any side effects.