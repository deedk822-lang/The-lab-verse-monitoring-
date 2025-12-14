#!/bin/bash

# This test script verifies the output of the `make help` command.
# It specifically checks for a bug where an extraneous, color-formatted
# blank line is printed before the list of targets.

echo "--- Running test: test_makefile_help.sh ---"

# The bug is an extra line containing only ANSI color codes.
# We use grep with:
# -F: Treat pattern as a fixed string, not a regex.
# -q: Quiet mode, just exit with status 0 on match.
# -x: Match the entire line exactly.
#
# The string $'\e[36m\e[0m' is the bash representation of the
# exact characters printed by the buggy `printf` statement.
# We redirect make's stderr to /dev/null to hide the expected "Broken pipe" error.
if make help 2>/dev/null | grep -F -q -x $'\e[36m\e[0m'; then
    echo "TEST FAILED: Bug found. 'make help' is printing an extraneous empty line."
    exit 1
else
    echo "TEST PASSED: Bug not found. 'make help' output is clean."
    exit 0
fi