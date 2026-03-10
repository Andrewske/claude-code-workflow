# Fix Failing Tests

Run the test suite and create a systematic plan to fix all failures.

## Instructions

1. **Run the test suite** and capture all output:
   ```bash
   bun test 2>&1
   ```

2. **Parse the output** to identify:
   - Total tests run
   - Number of failures
   - Each failing test: file path, test name, error message, stack trace

3. **For each failing test**, analyze:
   - Error type (assertion, mock, import, timeout, etc.)
   - Root cause hypothesis
   - Required fix

4. **Create a fix plan** as a todo list with:
   - One item per failing test
   - Include file path and test name
   - Brief description of the fix needed

5. **Execute the plan**:
   - Fix tests one at a time
   - Re-run the specific test after each fix to verify
   - Mark todo as complete when test passes

## Notes

- Use the `bun-test-expert` skill for debugging patterns
- Mock setup must come BEFORE imports (common issue)
- Check `bun-test-setup.ts` for global test configuration
- Run `bun test -t "pattern"` to run specific tests

## Arguments

$ARGUMENTS - Optional: specific test file or pattern to run (default: all tests)
