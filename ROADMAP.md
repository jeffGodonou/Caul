# Caul learning roadmap

Build one milestone at a time. The current code is **Milestone 1** only; the
other features are deliberately not implemented yet. After each milestone,
run its checks, try it by voice, and fix any failure before continuing.

## Milestone 1 — Hear and speak (implemented)

- **Build:** microphone input, speech-to-text, local text-to-speech, greeting,
  echo, and a spoken exit command.
- **Learn:** functions, strings, imports, a `while` loop, and handling expected
  audio/recognition errors.
- **Check:** run the unit tests, then say "hello", a sentence, and "goodbye".
- **Done when:** all three spoken checks work and goodbye exits cleanly.

## Milestone 2 — Recognize commands

- **Build:** split command handling into a small `respond` function and add
  help, the current time, and unknown-command responses.
- **Learn:** conditionals, exact phrase matching, and keeping input and response
  logic separate.
- **Check:** add tests for each phrase without using a microphone; verify that
  a sentence containing "hi" does not accidentally trigger a greeting.
- **Done when:** each supported phrase has a passing test and unrelated phrases
  get a helpful response.

## Milestone 3 — Search the web and YouTube

- **Build:** Google searches and YouTube searches, with correctly encoded
  search terms opened in the default browser.
- **Learn:** URL encoding, extracting a search query, and injecting browser
  behavior so it can be tested without opening a real browser.
- **Check:** test spaces and punctuation in queries; confirm tests never launch
  a browser.
- **Done when:** the browser opens the expected search URL for both services.

## Milestone 4 — Open approved apps and websites

- **Build:** an explicit allowlist for a few common apps and websites.
- **Learn:** dictionaries, process launching, and why spoken input should not
  be run as an arbitrary shell command.
- **Check:** test each allowed target and verify an unrecognized app is refused.
- **Done when:** only allowlisted targets can be opened.

## Milestone 5 — Weather and music

- **Build:** location-aware weather search and Spotify music search.
- **Learn:** extracting optional details from commands and building URLs safely.
- **Check:** test a named location, no location, and a song title with
  punctuation.
- **Done when:** each request opens a useful result and Caul describes what it
  did.

## Milestone 6 — Calculator and a game

- **Build:** basic spoken arithmetic and rock-paper-scissors.
- **Learn:** parsing, input validation, numeric edge cases, and random choices.
- **Check:** test each operation, invalid input, division by zero, all game
  outcomes, and unrecognized moves.
- **Done when:** invalid input never crashes the listening loop.

## Milestone 7 — Make it dependable

- **Build:** settings, clearer recovery from microphone/network failures,
  optional logging, and startup instructions suited to your computer.
- **Learn:** configuration, error boundaries, and packaging a small Python app.
- **Check:** exercise a missing microphone, unavailable internet, and normal
  startup; run the full test suite after each change.
- **Done when:** setup and recovery instructions have been tested on your
  computer.

## A repeatable build-and-correct cycle

For every milestone:

1. Read the goal and the new Python idea before editing.
2. Add one small behavior, then write or update its test.
3. Run `python -m unittest discover -s tests -v`.
4. Try the behavior by voice if it uses the microphone.
5. If it fails, keep the failing example, fix one cause, and rerun the same
   checks plus the full test command.
6. Move on only when the milestone's **Done when** condition is met.

Keep changes small enough that you can explain what each changed function does.
