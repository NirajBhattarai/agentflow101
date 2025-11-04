# Contributing Guide (Quick Start)

Follow these steps to create a branch, commit your changes, push, and open a Pull Request (PR).

## 1) Clone and setup
```bash
git clone <REPO_URL>
cd agentflow101
git fetch origin
git checkout main
git pull origin main
```

## 2) Create a new branch
Use a short, descriptive branch name.
```bash
git checkout -b feature/<short-description>
# example: git checkout -b docs/add-contributing-guide
```

## 3) Make your changes
Edit files and run local checks if available.
```bash
# optional examples
make help
make dev
```

## 4) Stage and commit
Write a clear, conventional commit message.
```bash
git add -A
git commit -m "docs: add contributing guide with PR steps"
```

## 5) Push your branch
```bash
git push -u origin feature/<short-description>
```

## 6) Open a Pull Request (PR)
1. Go to your repository hosting (e.g., GitHub) in the browser.
2. You should see a prompt to open a PR from your branch.
3. Fill in the title and description (what, why, how to test).
4. Submit the PR for review.

## 7) Keep your PR up to date (if needed)
If `main` changes while your PR is open, update your branch:
```bash
git checkout main
git pull origin main
git checkout feature/<short-description>
git rebase main   # or: git merge main
git push --force-with-lease   # only if you rebased
```

## 8) Address review feedback
Push more commits to the same branch. They will appear in the PR automatically.

---

Tips:
- Configure your identity once per machine: `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`.
- Use small, focused commits.
- Run `make lint`/`npm run lint` (if available) before pushing.