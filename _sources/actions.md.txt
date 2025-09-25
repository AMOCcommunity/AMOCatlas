# Extra GitHub features: Actions & Pages

In this GitHub repository, we are using GitHub Actions to carry out a number of automated tasks. These actions are stored within the repository in the hidden folder: `.github/workflows/`.  The yaml files within (e.g., `docs.yml` and `pypi.yml`) carry out a set of steps or actions when triggered by an event on GitHub.

For example:

- On pull request, the actions `docs.yml` and `tests.yml` are triggered.
- On push (when a pull request is merged onto the upstream main), the action `docs_deploy.yml` is triggered.
- When a release is generated on Github, the action `pypi.yml` is triggered.

The basic behaviour is explained in the template repository that this project was built on at [http://github.com/eleanorfrajka/template-project/](http://github.com/eleanorfrajka/template-project) or in the docs at [https://eleanorfrajka.github.io/template-project/github.html](https://eleanorfrajka.github.io/template-project/github.html).


## This project's Actions

The way that this project ([http://github.com/AMOCcommunity/amocatlas](http://github.com/AMOCcommunity/amocatlas)) is set up:

- the `docs.yml` attempts to build the documentation which is contained in `docs/source/` and built to `docs/build/`.  It sets up the environment based on `requirements-dev.txt`, installs the project with `pip install`, and builds the documentation including running the `notebooks/demo.ipynb`.

- the `tests.yml` uses `pytest` to run the tests contained within the `tests/` directory, and it does this on several platforms (windows, mac and linux) and with a couple versions of python.

- the `docs_deploy.yml` is like `docs.yml` but additionally moves the resultant files onto the branch `gh-pages`.  Because of how we've set up the "Pages" of this repository ([https://github.com/AMOCcommunity/amocatlas/settings/pages](https://github.com/AMOCcommunity/amocatlas/settings/pages)), it updates the website that is hosted on github at [https://amoccommunity.github.io/amocatlas/](https://amoccommunity.github.io/amocatlas/).

- the `pypi.yml` is triggered on a release, and it uses the information in `pyproject.toml` and builds a distribution (see lines like `python -m build -sdist --wheel . --outdir dist`) into the `dist/` directory.  In order for this to run properly, several other steps need to be set up e.g., on [https://pypi.org/project/amocatlas/](https://pypi.org/project/amocatlas/), including setting a trusted publisher so that the Github Action is allowed to publish to this project on pypi.


## For contributors

Most of the setup has been taken care of already.  What is useful to know as a contributor?

When you make a pull request (PR), Github will try to build the docs and run the tests.  Sometimes these are hard to troubleshoot online, or maybe you'd like to test them before making your pull request to fix some of the bugs.

### Check `demo.ipynb`

Before making a PR, you can try to run `demo.ipynb` on your fork/branch to see whether it will run through.  Make sure you have the environment activated, restart the kernel, and then try a "run all".  If it works without throwing errors, then it should also work on Github.

### Check tests

You can run the tests locally if your environment is built from `requirements-dev.txt`.  Here we've also required e.g., `pytest`.

To run the tests, in the command line on your computer, activate the environment, make sure requirements from `requirements-dev.txt` are installed, and then run `pytest`.

For me, this looks like
```bash
cd github/amocatlas
virtualenv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Check what is failing.

### Build docs

To build the docs locally, you will also need to have an environment with the development requirements installed.  These include:
```
sphinx
sphinx-rtd-theme
pypandoc
nbsphinx
nbconvert
myst-nb
```

When you'd like to test the build of your documentation (prior to submitting pull requests to the repository), navigate to the `docs/` directory in a terminal window, and run
```
cd github/amocatlas/docs
make html
```
This will generate the website within the directory `docs/build/html/`, which you can open from a browser to verify that everything worked.

## For maintainers

If you also have the rights/inclination to publish a release to PyPi, you can test this before creating the release on GitHub.  There's also a slightly finicky set of steps that needs to be done in a special order to make sure the GitHub "tag" matches the PyPi "version".

### Build distribution

First go to the directory where your repository is located (i.e., where `pyproject.toml` is located):
```
cd github/amocatlas
```

To build the distribution locally, make sure you have the latest version of `build` installed:
```
python3 -m pip install --upgrade build pip wheel setuptools setuptools_scm build twine
```

Then run the build step from the directory where `pyproject.toml` is located,
```
python3 -m build --sdist --wheel . --outdir dist
```
You can check this with
```
ls dist
python -m twine check dist/*
```

You can also verify the version number
```
more amocatlas/_version.py
```

### Publishing a release

1. **On Github.com, upstream main:** Ensure all desired changes are merged into the `main` branch.  So, after you do a PR from your branch to the upstream main, resolve any problems and "merge", then you're ready to go.

![image from github.com showing the merge button](/_static/merge.jpg)

2. **On Github.com, your forked main:** If you're working from a branch (e.g., `yourname-patch-21`) of your fork (http://github.com/YOUR_USERNAME/amocatlas) of the upstream main (http://github.com/AMOCcommunity/amocatlas), then you'll want to sync your main to the upstream main.  On github.com, at http://github.com/YOUR_USERNAME/amocatlas, you should see that your main is "X commits behind".  There is a button where you can sync.

![image from github.com showing the sync fork button](/_static/sync_fork.jpg)

3. **On your computer, terminal:** In your repository directory, checkout main and pull any changes:
```
cd github/amocatlas
```
```
git checkout main
git pull
```

4. **On your computer, terminal** Same place, but now we're going to create the tag.  First make a note of the last tag.  On Github.com, the upstream main, you can check what tags have already been used (i.e., https://github.com/AMOCcommunity/amocatlas/tags).

The usual process is to start with a `vX.Y.Z` and possibly have an "alpha" or "beta" following as `vX.Y.Za2`.  These are called PEP440 style versioning, with an alpha prerelease tag (`a1`=alpha 1).  The "X" indicates a big change, the "Y" a minor change, and the "Z" a patch or little fix.

`MAJOR.MINOR.PATCH[pre-release]`

- **MAJOR**: Backward-incompatible changes
  Increment when you make changes that break existing APIs or data formats.
  Example: changing function signatures, renaming modules, or changing expected output structures.
- **MINOR**: Backward-compatible feature additions
  Increment when you add new functionality in a backward-compatible way.
  Example: adding a new reader (read_xyz.py), adding new plotting functions, or expanding metadata handling.
- **PATCH**: Backward-compatible bug fixes or internal improvements
  Increment for fixes or improvements that don't add features or break existing code.
  Example: fixing a unit conversion error, improving docstrings, or cleaning up warnings.

Increment the appropriate one based on the change you're making, and pick the next available tag.  So a pre-release change if we're at `v0.0.2a6` would mean your next version should be indicated with tag `v0.0.2a7`.  Assuming this, the next steps are:

Quick check that you're on the last commit.  The output from this should be your commit message from the PR.
```
git log -1
```

Then tag this version using:
```
git tag v0.0.2a7
git push upstream v0.0.2a7
```

This step assigns the tag and then pushes it to the upstream main.  Go onto Github.com and check that this tag is now there: https://github.com/AMOCcommunity/amocatlas/tags.

5. **On Github.com**

- Go to the **Releases** tab.

- Click **"Draft a new release."**

- Choose the tag you just pushed (e.g. `v0.0.2a7`) from the dropdown.

- Fill in (or auto-generate) the release notes & edit if necessary.

- Click **"Publish release."**

This last step will now trigger the GitHub action, `.github/workflows/pypi.yml` which will build the distribution and send it to pypi.org.  You should see this show up at [https://pypi.org/project/amocatlas/](https://pypi.org/project/amocatlas/).

**Note:** Unexplained behaviour may occur (e.g., you get a `dev0` appended to the release on pypi) if you are not at the tip of main (i.e. there are uncommitted changes), or you haven't included `amocatlas/_version.py` in your `.gitignore`, in which case the action itself generates a change in the repository which is then interpreted as an uncommitted change.
