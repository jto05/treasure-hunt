# Contributing

Steps for working on this repo with git and GitHub.

## One-time setup

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
git clone https://github.com/jto05/treasure-hunt.git
cd treasure-hunt
```

## Workflow

`master` is protected — you can't push to it directly. Every change goes
through a branch and a pull request:

```bash
git checkout master && git pull          # 1. get latest master
git checkout -b your-name/short-desc     # 2. branch
# ...edit files...
git add <files>                          # 3. stage
git commit -m "prefix: short description"
git push -u origin your-name/short-desc  # 4. push
```

Then on GitHub: open a pull request (click the yellow banner, or **Pull
requests → New pull request**), wait for the green check (`server-tests`),
click **Squash and merge**, then **Delete branch**.

Clean up locally: `git checkout master && git pull && git branch -d
your-name/short-desc`.

## Commit prefixes

Start every commit message with one of:

| Prefix | Use for |
|---|---|
| `feat:` | a new feature or capability |
| `fix:` | a bug fix |
| `doc:` | documentation only |
| `test:` | adding or fixing tests, no behavior change |
| `refactor:` | restructuring code, no behavior change |
| `chore:` | maintenance (deps, `.gitignore`, config) |
| `ci:` | GitHub Actions / CI changes |
| `style:` | formatting-only changes |

Example: `feat: add hold_zone challenge type`

## Keeping your branch up to date

If master moves on while you're still working:

```bash
git checkout master && git pull
git checkout your-name/short-desc
git rebase master
```

Conflict? Git names the file(s) — edit out the
`<<<<<<<`/`=======`/`>>>>>>>` markers, then `git add <file> && git rebase
--continue`. Stuck? `git rebase --abort` and ask in the group chat.

## Pruning your local repo

Every merged PR deletes its branch on GitHub, but your local clone
doesn't know that until you tell it. Every so often (or whenever `git
branch` looks cluttered):

```bash
git fetch --prune              # drop local refs to branches deleted on GitHub
git branch --merged master     # list local branches already merged into master
git branch -d old-branch-name  # delete one (repeat, or script it)
```

`-d` (not `-D`) refuses to delete a branch with unmerged work, so it's
safe to run without checking each one by hand first.

## Quick reference

| Command | What it does |
|---|---|
| `git status` | what's changed, what's staged |
| `git diff` | line-by-line changes |
| `git checkout -b name` | create + switch to a new branch |
| `git add <file>` | stage a file |
| `git commit -m "msg"` | commit staged changes |
| `git push -u origin name` | push a new branch (first time) |
| `git pull` | get latest changes |
| `git fetch --prune` | clean up refs to deleted remote branches |

## If something feels broken

`git status` first. Don't guess with `git reset --hard`, `git checkout --
.`, or `git clean` — ask first. There's no undo.
