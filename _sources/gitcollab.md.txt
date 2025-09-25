# Collaborating with git: Basic workflow

See also, the description of actions in https://github.com/eleanorfrajka/template-project/pull/1.

The instructions below assume that you would like to contribute to https://github.com/AMOCcommunity/amocatlas

### Forking & branching someone else's repository

Suppose the original repository is located at: https://github.com/AMOCcommunity/amocatlas, and you would like to contribute to it.  This repository located on the web at http://github.com/AMOCcommunity is the **upstream main** and is "owned" by the organisation "AMOCcommunity", at https://github.com/AMOCcommunity.

When you first work with a shared repository, you will want to:

#### 1. Fork the repository

**On Github.com:** Login with your Github username.  Navigate to the **upstream main** ([https://github.com/AMOCcommunity/amocatlas](https://github.com/AMOCcommunity/amocatlas)) and click the "fork" button near the top right.  This will fork the repository into your own Github account, meaning it will create a complete copy of the repository in your account, located online at `https://github.com/YOUR_USERNAME/amocatlas`.  If prompted, specify that you would like to *contribute to the original project*.  Initially, this new repository is **your forked main**.

For the way we recommend to work, the only thing you will do in your **forked main** is "sync" the changes with the **upstream main**.  "main" refers to which branch of the repository you're talking about.  There may be several, but when you first start, you'll only have a "main".   You should do this before working on the repository to bring in any changes that were "pulled" onto the upstream main to your forked main.

#### 2. Clone to your computer

**On Github.com:** From your forked repository, clone the repository to your computer.

(i) Navigate to your repositories on GitHub, `https://github.com/YOUR_USERNAME/amocatlas`.  Click the green `<> Code` dropdown button, and choose a method to clone this.  If you're not familiar with cloning repositories to your computer, choose `Open with Github Desktop` which will require you to have the application "GitHub Desktop" on your computer.

(ii) When prompted, choose where on your computer you would like this to live (`/a/path/on/your/computer/`).

This is your **local repository** of your github repository.

> **Tip**
> If you use a cloud backup service, do *not* put this in a folder that is synced with the cloud. This is because the online backups via a cloud service will need to keep copying files back and forth when you switch branches (which replaces the files in your active directory with the versions from each branch), and depending on timing, the synchronisation could cause errors or duplication.  Additionally, using git negates much of the need for cloud backups as local commits *and* pushes to the online git repository provides backups by design.

#### 3. Find the clone on your computer

**On your computer in File Explorer (Windows) or Finder (Mac):** Now you have a copy of the repository on your computer, with the associated "git" tracking information.  The repository already knows the history of changes, and has the necessary structure to update.  These are in a hidden folder within the repository folder (likely called `/a/path/on/your/computer/amocatlas/.git`).   This is a "main" branch of your forked repository `https://github.com/YOUR_USERNAME/amocatlas`.

So now there are 3 copies of this repository:
- the **upstream main** at http://github.com/AMOCcommunity/amocatlas
- your **forked repository** at `http://github.com/YOUR_USERNAME/amocatlas`
- your **local repository** on your computer at some `/a/path/on/your/computer/amocatlas/`

The following process describes how to keep these working smoothly together.  The short version is, you'll be working on a *feature branch* of your **local repository** (not the main, never the main).  When you have a set of changes you like and have committed (which stores discrete update information in your `.git/`), then you will initiate a "pull request" to the **upstream main**.  I.e., you skip your online forked repository entirely.  This triggers a change on http://github.com/AMOCcommunity/amocatlas which can be seen in the "pull requests" menu.  Once this has been dealt with (more below), you will "merge" your changes with the **upstream main** which is also a "push to main".  This updates http://github.com/AMOCcommunity/amocatlas with the latest changes that you'd made in your *feature branch* on your computer.  Now, your **forked repository** is "behind" the **upstream main**, so you need to sync it to bring the changes into your fork.  And then you need to "pull" these changes onto your **local repository** with a `git checkout main; git pull`.  This will then ensure that your local computer has the latest changes from the **upstream main**.  Finally, you need to checkout a new *feature branch* to continue making changes.

#### 4. Create a *feature branch* or just "branch" for edits

**On Github.com:** First make sure your **forked main** is up-to-date with the **upstream main**.  Navigate to your repository, `http://github.com/YOUR_USERNAME/amocatlas` (refresh the page if you already had it open), and check whether it says "This branch is up to date with AMOCcommunity/amocatlas:main".  If it does, then you're already synced and good to go.  If not, then you need to click the "sync fork" button to update.

**On your computer in a terminal window:** When you'd like to start making changes in your repository, **first** make a new branch. For a forked repository (`http://github.com/YOUR_USERNAME/amocatlas`) from someone else's original upstream repository (http://github.com/AMOCcommunity/amocatlas), you will *never* work in your forked main branch.

To make a branch, at the command line, the series of steps would be (from within `/a/path/on/your/computer/amocatlas/`):
```
$ git checkout main
$ git pull
$ git checkout -b yourname-patch-1
```
where you change "yourname" to your first name (or other useful identifier, e.g. your GitHub username).  (If you're not sure what "branches" you've already created, you can run a `git branch` to see, and increment the number by 1.)

This new **feature branch** will now be up-to-date with the latest changes within your **forked main** (which is what the `git pull` command does), but will have a separate copy for you to make your edits in.

> **Suggested naming convention:** `yourfirstname-patch-#` where `#` increments by one for each new branch you make.  Some people also name branches by the topic or issue that branch is addressing.  So far, I've found for early code development that I'll intend a branch for one purpose, but find another that should be fixed/changed first, and then I have a branch name called `eleanor-docs-1` but it's really about a new test of plotters (or something).

#### 5. Make an edit in the branch

**On your computer in VS Code (or wherever you work on Python):** Make a change to a file.  Even adding an extra line of whitespace will do this.  Then save the file.

#### 6. Commit the change in your branch

**In VS Code**, to commit the change, you will navigate to the "source explorer" in the left hand bar, and add a commit message (text box above the blue "Commit" button).  This should be short and informative, explaining in present tense what the commit does.

> **Optional (recommended):** Add a short code at the beginning of the commit message (one word) to help categorise what the commit is doing.  See [https://dev.to/ashishxcode/mastering-the-art-of-writing-effective-github-commit-messages-5d2p](https://dev.to/ashishxcode/mastering-the-art-of-writing-effective-github-commit-messages-5d2p).

> Options include things like:

> - `feat: <extra text explaining more detail>` when you're adding a new feature or functionality
> - `fix: <extra text explaining more detail>` when you're committing a fix for a specific problem or issue
> - `style:` when you're making changes to style or formatting but not functionality (user should experience no change)
> - `refactor:` changes to the code that improve structure or organisation, but don't add features or fix bugs
> - `test:` when you're adding or updating tests for the code
> - `chore:` updating changes to the build process or other tasks not directly related to the code (e.g., GitHub workflows)
> - `perf:` Changes to improve code performance, e.g. speed
> - `ci:` changes to the continuous integration process

#### 7. Create a pull request to **upstream main**

**On your computer in VS Code:** Sync the commit to main.  If this is the first time you've done this from your branch, you will need to "set the upstream".  Set the upstream to be https://github.com/AMOCcommunity/amocatlas.  This will direct the pull request to the **upstream main** repository (not your main). If you accidentally set it to your main, no worries, it just created a branch on your **forked repository** that won't go anywhere.  Redo it to upstream.

Don't worry, if you created a pull request by mistake, you can "close it" on github.com without doing anything further.

#### 8. Compare pull request on GitHub.com

**On Github.com (original/upstream repository):** Navigate to the original repository https://github.com/AMOCcommunity/amocatlas and you should see the pull request has come through.  There will be a shaded bar at the top with a button "compare and pull request".  Click this button and on the next page add some useful details for the rest of the contributors to understand what your commit is doing.

Note that the default version of this template includes some tests to be run when you submit a pull request.  The python code for these tests is located in `tests/`.  The Github Actions "workflow" that calls the tests is in `.github/workflows/tests.yml`.  It requires that your `requirements-dev.txt` file includes the package:
```
pytest
pytest-cov
```

#### 9. Merge the pull request

**On Github.com (original repository):** Navigate to the original repository https://github.com/AMOCcommunity/amocatlas.  Once your edits have passed all tests, a review from a repository owner (if required) and been approved, then *you* (as the originator of the change) can "merge".  This will "push" your changes onto the **upstream main** branch.

Recommended (optional): If you find that you make a lot of incremental commits--like (1) you committed something, then realised you forgot to clear all outputs on your python notebook and want to re-save and commit, or (2) you made a change and committed it, then realised you had to update another function to be compatible so went and changed that then committed it--you may want to "Squash and Merge". This will turn the 5 (or 10 or 20) commits in your pull request into a single commit, which cleans up the history of the software.

If you have a lot of distinct commits with different purposes in the same PR, you may *not* want to squash and merge.

#### 10. Rinse and repeat

Now the origin has been updated.

**On Github.com (your forked repository):** If you want to make further changes *after a merge (by anyone)*, you should **first** sync your fork (main branch) to the origin.

1. On your forked repository main, `https://github.com/YOUR_USERNAME/amocatlas` where you should see a notification across the top saying "this is behind the origin/main by X commits" with the option to click the **sync** button.  Click it!  This gets your forked main branch _on Github_ up-to-date with the origin/main.

2. **On your computer, terminal window:** After syncing your fork to the origin's main on GitHub.com, the next step is to pull any new changes onto your fork's main branch _on your computer_.

```
$ git checkout main
$ git pull
```

3. **On your computer, terminal window:** Now you need to create a new branch for working _on your computer_.
As before, create a new branch using `git checkout -b branchname` as in:
```
$ git checkout -b yourname-patch-2
```
This will create a new branch `yourname-patch-2` based on the new, updated main on your computer.  The `-b` option creates a branch (without `-b`, it will try to switch to a branch with that name).

Now you're ready to repeat from step 5.

> **Note:** If you forgot to sync your fork (main branch), and then have a new pull request, you may have merge have conflicts when pulling any changes to the main/origin.
