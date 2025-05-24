# GitHub Repository Setup

This document contains instructions for pushing this project to GitHub.

## Push to GitHub

1. If you haven't already initialized git in this repository, run:

```bash
git init
```

2. Stage all files:

```bash
git add .
```

3. Create your first commit:

```bash
git commit -m "Initial commit: Fireflies Raycast Extension"
```

4. Add the GitHub repository as a remote:

```bash
git remote add origin https://github.com/culstrup/fireflies-raycast.git
```

5. Push to GitHub:

```bash
git push -u origin main
```

If your default branch is master instead of main:

```bash
git push -u origin master
```

## What's Next

After pushing to GitHub:

1. Go to your GitHub repository settings to:
   - Add a description
   - Set up GitHub Pages if desired
   - Configure branch protection rules

2. Add screenshots to the `screenshots` directory, then update the README to remove the placeholder note.

3. Share your repository with others!

## Updating Your Repository

When you make changes:

```bash
git add .
git commit -m "Describe your changes"
git push
```
