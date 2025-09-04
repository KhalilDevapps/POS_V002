# Git and GitHub Guide for POS Project

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Basic Git Workflow](#basic-git-workflow)
4. [Pushing to GitHub](#pushing-to-github)
5. [Pulling from GitHub](#pulling-from-github)
6. [Common Scenarios](#common-scenarios)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you start, make sure you have:
- Git installed on your system
- A GitHub account
- Your project initialized as a Git repository

### Check Git Installation
```bash
git --version
```

### Check if Git is Initialized
```bash
git status
```

## Initial Setup

### 1. Configure Git (First Time Only)
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 2. Initialize Git Repository (if not already done)
```bash
git init
```

### 3. Add Remote Repository
```bash
git remote add origin https://github.com/KhalilDevapps/POS.git
```

## Basic Git Workflow

### 1. Check Repository Status
```bash
git status
```

### 2. Add Files to Staging
```bash
# Add all files
git add .

# Add specific files
git add app.py
git add templates/
```

### 3. Commit Changes
```bash
git commit -m "Your commit message here"
```

## Pushing to GitHub

### Method 1: First Time Push (when repository is empty)
```bash
# Add all files
git add .

# Commit changes
git commit -m "Initial commit"

# Push to main branch
git push -u origin main
```

### Method 2: Regular Push (after making changes)
```bash
# Check status
git status

# Add changes
git add .

# Commit changes
git commit -m "Description of changes"

# Push to GitHub
git push
```

### Method 3: Force Push (use with caution)
```bash
# Force push (overwrites remote)
git push --force origin main
```

## Pulling from GitHub

### Method 1: Regular Pull
```bash
# Pull latest changes
git pull origin main
```

### Method 2: Pull with Rebase (cleaner history)
```bash
git pull --rebase origin main
```

### Method 3: Fetch and Merge Separately
```bash
# Fetch changes from remote
git fetch origin

# Merge changes
git merge origin/main
```

## Common Scenarios

### Scenario 1: Working with Multiple People
```bash
# Always pull before starting work
git pull origin main

# Make your changes
# ... edit files ...

# Add and commit
git add .
git commit -m "Your changes"

# Push
git push origin main
```

### Scenario 2: Resolving Merge Conflicts
```bash
# Pull latest changes
git pull origin main

# If conflict occurs, edit conflicted files
# Look for conflict markers: <<<<<<<, =======, >>>>>>>

# After resolving conflicts
git add .
git commit -m "Resolved merge conflicts"
git push origin main
```

### Scenario 3: Working on a Feature Branch
```bash
# Create new branch
git checkout -b feature/new-feature

# Make changes
git add .
git commit -m "Feature implementation"

# Push branch to GitHub
git push -u origin feature/new-feature

# Later, merge to main
git checkout main
git pull origin main
git merge feature/new-feature
git push origin main
```

## Branch Management

### View Branches
```bash
# List all branches
git branch -a

# See current branch
git branch
```

### Switch Branches
```bash
git checkout branch-name
```

### Create New Branch
```bash
git checkout -b new-branch-name
```

### Delete Branch
```bash
# Delete local branch
git branch -d branch-name

# Delete remote branch
git push origin --delete branch-name
```

## Troubleshooting

### Problem: "fatal: remote origin already exists"
```bash
# Remove existing remote
git remote remove origin

# Add new remote
git remote add origin https://github.com/KhalilDevapps/POS.git
```

### Problem: "fatal: not a git repository"
```bash
# Initialize git repository
git init

# Add remote
git remote add origin https://github.com/KhalilDevapps/POS.git
```

### Problem: "Permission denied"
```bash
# Check if you have push permissions
# Make sure you're using the correct repository URL
git remote -v

# If using SSH, ensure your SSH key is configured
# If using HTTPS, you might need to use a personal access token
```

### Problem: "Updates were rejected because the remote contains work"
```bash
# Pull latest changes first
git pull origin main --rebase

# Then push
git push origin main
```

### Problem: Lost Changes
```bash
# View commit history
git log --oneline

# View changes in a specific commit
git show commit-hash

# Create new branch from previous commit
git checkout -b recovery commit-hash
```

## Useful Git Commands

### View History
```bash
# Basic log
git log

# Compact log
git log --oneline

# Log with graph
git log --graph --oneline --all
```

### Undo Changes
```bash
# Unstage files
git reset HEAD file.txt

# Discard changes in working directory
git checkout -- file.txt

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

### Stashing Changes
```bash
# Save changes temporarily
git stash

# List stashes
git stash list

# Apply stashed changes
git stash apply

# Apply and remove stash
git stash pop
```

## Best Practices

1. **Commit Often**: Make small, frequent commits with clear messages
2. **Pull Before Push**: Always pull latest changes before pushing
3. **Use Branches**: Work on features in separate branches
4. **Write Good Commit Messages**: Use clear, descriptive messages
5. **Don't Commit Sensitive Data**: Never commit passwords, API keys, etc.
6. **Review Changes**: Use `git diff` to review changes before committing

## Quick Reference

```bash
# Daily workflow
git status              # Check status
git add .              # Stage all changes
git commit -m "msg"    # Commit changes
git pull origin main   # Pull latest
git push origin main   # Push changes

# Emergency commands
git reset --hard HEAD  # Discard all changes
git clean -fd          # Remove untracked files
git reflog             # View recent actions
```

---

**Note**: This guide assumes you're using the `main` branch as your primary branch. If your repository uses `master`, replace `main` with `master` in all commands.

For more advanced Git features, consider learning about:
- Git rebase
- Git cherry-pick
- Git bisect
- Git hooks
