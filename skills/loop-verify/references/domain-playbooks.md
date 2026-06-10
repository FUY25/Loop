# Domain verification playbooks

Standard end-to-end passes per domain. Use as the default the user edits, and as the source of
implicit checks to add to their stated workflow. In every playbook: capture evidence, check
regression scope, report failures faithfully.

## Web UI
- Start the dev server; confirm it boots clean (no build errors in output).
- Drive the page like a user: navigate, click the changed feature, fill forms with realistic
  values. Tools: Claude Preview / Chrome extension / Chrome DevTools MCP / headless browse —
  whichever the project already uses.
- Read the browser console — zero new errors/warnings is the bar.
- Screenshot the changed state (and before/after when layout changed).
- Core Web Vitals / layout-shift trace when the change touches rendering or assets.
- Responsive spot-check at one mobile width if the project has mobile users.
- Regression scope: the page's other primary interaction + one adjacent route.

## API / backend
- Boot the service; hit the changed endpoint with a realistic payload (curl/httpie).
- Assert status code AND response shape (schema/keys, not just 200).
- One unhappy-path call: bad input → expected 4xx, not a 500.
- Check service logs for new warnings/stack traces during the calls.
- Idempotency: repeat the same mutating call; verify no duplicate side effects where contract
  says idempotent.
- Regression scope: one upstream caller flow of the changed endpoint.

## CLI tools
- Run the changed command with typical args; assert exit code and key output lines.
- Run `--help`; confirm flags documented match behavior.
- One failure case: missing/invalid arg → useful error message, nonzero exit.
- Pipe-ability if relevant: stdout is clean data, diagnostics go to stderr.
- Regression scope: the most-used sibling subcommand.

## Docs / content
- Build the docs (or render the markdown); zero build warnings.
- Click every link added/changed; verify anchors resolve.
- Run code snippets that were added/changed — snippets that don't run are anti-docs.
- Spot-check rendering of tables/images in the built output, not the source.

## Data pipeline
- Run on a small fixture input; diff output against expected (commit the fixture).
- Row counts and key invariants (no nulls in key columns, totals reconcile) asserted, not eyeballed.
- Re-run on the same input: identical output (determinism check).
- Check for silent drops: input rows - output rows must be explained.
- Regression scope: one downstream consumer's read of the output schema.
