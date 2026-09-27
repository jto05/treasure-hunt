# Contributing

A step-by-step guide for working on this repo with git and GitHub. If
you've never used git before, follow this literally, top to bottom, the
first few times — it'll feel mechanical at first and then click.

## One-time setup

1. Install git if you don't have it: `git --version` (if that errors,
   install it — macOS: `brew install git`; Windows: get it from
   [git-scm.com](https://git-scm.com/downloads); Linux: `sudo apt
   install git` or equivalent).
2. Tell git who you are (once, ever, per computer):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your@email.com"
   ```
3. Clone the repo (do this once):
   ```bash
   git clone https://github.com/jto05/treasure-hunt.git
   cd treasure-hunt
   ```

## The big picture

`master` is the shared, protected branch — the "real" copy of the
project. **You cannot push directly to it.** GitHub will reject it. This
is on purpose: it forces every change through a pull request (PR), which
runs automated tests and gives everyone else a chance to see the diff.

The workflow, every time you sit down to work:

```
1. Get the latest master
        ↓
2. Create a new branch for your change
        ↓
3. Make your changes, commit them
        ↓
4. Push your branch to GitHub
        ↓
5. Open a Pull Request (on github.com)
        ↓
6. Wait for the green checkmark (automated tests)
        ↓
7. Merge it ("Squash and merge" button)
        ↓
8. Delete the branch, go back to step 1
```

Never work directly on `master` in your local copy either — always
branch first (step 2). If you forget and start editing on `master`, git
will still let you commit, you'll just get stuck later; easier to just
always branch first out of habit.

## Step by step

### 1. Get the latest master

```bash
git checkout master
git pull
```

Do this every time you start something new, so you're not branching off
stale code.

### 2. Create a branch

```bash
git checkout -b your-name/short-description
```

Examples: `sam/hold-zone-challenge`, `priya/admin-status-endpoint`,
`jordan/fix-arp-parsing`. Doesn't need to be fancy — just something
that tells people what it's about. This creates the branch **and**
switches you onto it in one command.

### 3. Make your changes

Edit files like normal. Check what you've changed as you go:

```bash
git status      # what files did I touch?
git diff        # what exactly did I change?
```

### 4. Commit your changes

```bash
git add <file1> <file2>       # stage the specific files you changed
git commit -m "prefix: short description of the change"
```

Or, if you're sure you want to stage *everything* that changed:

```bash
git add -A
git commit -m "prefix: short description of the change"
```

Commit in small, logical chunks rather than one giant commit at the end
— e.g. one commit for the server change, a separate one for its tests,
rather than both jammed together with everything else you touched that
day.

**Commit message prefixes** — start every commit message with one of
these, so everyone can skim the log and understand a diff before reading
it (this is a workflow rule, not a git feature, so nothing enforces it
automatically):

| Prefix | Use for |
|---|---|
| `feat:` | a new feature or capability |
| `fix:` | a bug fix |
| `doc:` | documentation only (README, comments-as-docs, this file) |
| `test:` | adding or fixing tests, no behavior change |
| `refactor:` | restructuring code with no behavior change |
| `chore:` | maintenance stuff that isn't feature/fix/docs (deps, `.gitignore`, config) |
| `ci:` | changes to GitHub Actions / the CI pipeline |
| `style:` | formatting-only changes (whitespace, naming) with no logic change |

Examples:
- `feat: add hold_zone challenge type`
- `fix: correct MAC lowercasing in netinfo`
- `test: cover found-state reset on signal drop`
- `doc: describe /api/admin/config in server README`

If a change spans two of these, either split it into two commits, or
just pick whichever one is dominant.

### 5. Push your branch

```bash
git push -u origin your-name/short-description
```

The `-u` is only needed the first time you push that branch — it tells
git to remember the connection, so afterwards you can just run `git
push`.

### 6. Open a Pull Request on GitHub

1. Go to https://github.com/jto05/treasure-hunt.
2. GitHub usually shows a yellow banner: **"your-name/short-description
   had recent pushes"** with a **Compare & pull request** button. Click
   it. (If you don't see it: click the **Pull requests** tab → **New
   pull request** → pick your branch.)
3. Write a title (can just be your commit message if there's only one
   commit) and a short description of *what* and *why*.
4. Click **Create pull request**.

### 7. Wait for the check, then merge

After you open the PR, GitHub automatically runs the test suite
(`server-tests`). You'll see either:
- 🟡 a yellow dot — still running, wait a minute and refresh
- ✅ a green check — tests passed, you're good to merge
- ❌ a red X — something broke; click **Details** to see what, fix it,
  push another commit to the same branch (`git push`, no need to open a
  new PR — it updates automatically), and it'll re-run

GitHub won't let you merge until it's green — that's enforced
automatically, not optional.

Once it's green:
1. It's a good habit to tag a teammate to take a quick look, even though
   GitHub doesn't currently *require* an approval to merge.
2. Click **Squash and merge** (not "Create a merge commit" — this repo
   keeps history linear, and GitHub will complain if you try the other
   option). Confirm.
3. Click **Delete branch** on the confirmation screen — the branch has
   done its job.

### 8. Clean up locally and start the next thing

```bash
git checkout master
git pull
git branch -d your-name/short-description   # deletes your local copy of the merged branch
```

Now you're back at step 1 for the next change.

## Keeping your branch up to date

If you're working on a branch for a while and `master` moves on without
you (someone else merged first), bring your branch up to date before you
keep going, or before you open the PR:

```bash
git checkout master
git pull
git checkout your-name/short-description
git rebase master
```

If `rebase` reports a conflict, git will tell you which file(s); open
them, look for `<<<<<<<` / `=======` / `>>>>>>>` markers, edit to keep
what should actually be there, then:

```bash
git add <the file you fixed>
git rebase --continue
```

If it gets confusing, it's always fine to stop (`git rebase --abort`)
and ask someone rather than guessing.

## Quick reference

| Command | What it does |
|---|---|
| `git status` | what's changed, what's staged |
| `git diff` | line-by-line changes, unstaged |
| `git checkout -b name` | create + switch to a new branch |
| `git checkout name` | switch to an existing branch |
| `git add <file>` | stage a file for the next commit |
| `git commit -m "msg"` | commit staged changes |
| `git push -u origin name` | push a new branch the first time |
| `git push` | push again after the first time |
| `git pull` | get the latest changes for your current branch |
| `git log --oneline` | see recent commits, one line each |

## If something feels broken

`git status` first, always — it tells you what state you're in. Past
that, don't guess with destructive commands (`git reset --hard`, `git
checkout -- .`, `git clean`) if you're not sure what they do — ask in
the group chat first. Uncommitted work is easy to lose that way, and
there's no undo.
