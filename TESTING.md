# Testing

## Local setup (server/)

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
pytest
```

`requirements.txt` is the pinned list shared by the Pi, laptops and
Docker (see the root README). Appending `pytest` on the install line
works whether or not it's already listed there — Person 3's task list
has it landing in `requirements.txt` itself eventually, at which point
this is a no-op.

## What CI checks

`.github/workflows/server-tests.yml` runs `pytest` from `server/` on
every push to `master` and every pull request. `server/tests/` is still
empty scaffolding as of this writing, so pytest currently exits with
code 5 ("no tests collected") — the workflow treats that one exit code
as a pass so the pipeline isn't red before anyone's written a test. That
fallback stops doing anything once real tests exist; a genuine failure
(any other nonzero exit) still fails the build.

## Docker Compose simulation

Once `sim/` and the Flask server are implemented, `docker compose up` at
the repo root is the integration-level test harness — it stands up the
server, three simulated treasures, and simulated phones without any
hardware, per the **Development with Docker** section of the root
README. That's the place to check end-to-end behavior (registration,
hints, minigames, leaderboard) rather than in `server/tests/`, which is
for unit-testing `hunt/` in isolation.

## PR workflow

`master` is protected by a GitHub ruleset: pull requests are required,
history must stay linear, and force-push/delete are blocked. As of this
writing the ruleset does **not** require any approvals — the root
README's own working rule ("open a pull request, one other person
reviews it") isn't yet enforced by GitHub. Worth revisiting as a team if
you want that enforced automatically; not changed here since it's a
team-process decision, not a testing one.

## Adding a new test area

When `sim/` (or anything else) gets its own `tests/` folder and
`requirements.txt`, add a sibling job to `server-tests.yml` (or a new
workflow file) following the same shape: install that folder's pinned
requirements plus `pytest`, run `pytest` from inside that folder.
