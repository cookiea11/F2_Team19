# Publish the prepared repository

Use repository name **F2_Team19**. Authenticated GitHub access was not available
here, so no remote repository or verified URL is claimed.

## Browser method

1. Sign in to your GitHub account and create a repository named F2_Team19.
2. Choose public visibility only if your team is comfortable publishing its names,
   register numbers, source, and report. If private, grant the faculty access.
3. Extract F2_Team19_SourceCode.zip and generate the actual screenshots first.
4. Upload the folder contents, including source, docs, results, simulation, and screenshots.
5. Confirm README.md and app.py are at the repository root. Open the report,
   presentation, simulation configuration, and screenshots through GitHub.
6. Copy the actual repository URL into VTOP Assignment 10 after access verification.

## Git method

Create an empty GitHub repository without generating another README. In the
extracted project folder:

```sh
git init -b main
git add .
git commit -m "Add F2 Team19 routing project and evaluation"
git remote add origin YOUR_ACTUAL_GITHUB_REPOSITORY_URL
git push -u origin main
```

Replace the URL placeholder with the exact URL GitHub provides. Do not run it
literally. Use normal Git credential-manager or GitHub authentication. Never
store a token in the repository. Configure your own local Git author identity
if Git prompts for it.

Verify signed-out access for a public repository or the correct faculty account's
access for a private repository. Do not submit a guessed URL or an empty repository.

After screenshot capture:

```sh
git add screenshots
git commit -m "Add real dashboard screenshots"
git push
```
