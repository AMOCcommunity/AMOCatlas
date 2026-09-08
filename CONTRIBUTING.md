<!-- omit in toc -->
# Contributing to amocatlas

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them.


<!-- omit in toc -->
## Table of Contents

- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
- [Licensing of Contributions](#licensing-of-contributions)
- [Credit and Authorship](#credit-and-authorship)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)
- [Your First Code Contribution](#your-first-code-contribution)
- [Improving The Documentation](#improving-the-documentation)
- [Styleguides](#styleguides)
- [Commit Messages](#commit-messages)
- [Join The Project Team](#join-the-project-team)



## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://amoccommunity.github.io/AMOCatlas/).

Before you ask a question, it is best to search for existing [Issues](https://github.com/AMOCcommunity/amocatlas/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue. It is also advisable to search the internet for answers first.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Open an [Issue](https://github.com/AMOCcommunity/amocatlas/issues/new).
- Provide as much context as you can about what you're running into.
- If possible, try to provide a reproducible example, e.g. a jupyter notebook.
- Provide project and platform versions, depending on what seems relevant.

<!--
You might want to create a separate issue tag for questions and include it in this description. People should then tag their issues accordingly.

Depending on how large the project is, you may want to outsource the questioning, e.g. to Stack Overflow or Gitter. You may add additional contact and information possibilities:
- IRC
- Slack
- Gitter
- Stack Overflow tag
- Blog
- FAQ
- Roadmap
- E-Mail List
- Forum
-->

## I Want To Contribute

Please read the two short sections on licensing and credit before opening a pull request. They exist so that nobody has to have an awkward retrospective conversation about attribution — which, for a package whose whole product is correct attribution, matters more here than in most projects.

### Licensing of Contributions

amocatlas is MIT licensed (see `LICENSE`), and contributions are accepted **under the same licence** — what GitHub calls "inbound = outbound". By opening a pull request you confirm that:

1. you wrote the contribution, or you otherwise have the right to submit it; and
2. you agree to license it to the project under the MIT licence.

This does not transfer your copyright, which remains yours.

**If your contribution contains code or data from somewhere else** — another repository, a paper's supplementary material, a Stack Overflow answer, a colleague's script, or generated output you did not review line by line — say so in the pull request and name the source and its licence. This is the single most useful thing you can tell a reviewer. Code from an unlicensed or incompatibly-licensed source cannot be merged until that is resolved, so flagging it early avoids wasted work.

### Credit and Authorship

Three separate things, often confused:

**Copyright** stays with whoever wrote the code. You are not asked to assign it.

**Contributor credit** is automatic. Everyone whose pull request is merged appears in the git history. If your name or preferred email in the git log is wrong, open an issue or a PR to correct it.

**Citation authorship** is the author list in `CITATION.cff`, which propagates into the Zenodo/GitHub citation record for every release and therefore into other people's bibliographies. It reflects *substantial* contribution to the software — its design, a significant body of its implementation, its test suite, or its documentation architecture — and is decided by the maintainers at release time. Funding or supervision alone does not qualify. There is no line count that guarantees it and none that excludes it: a well-designed module that fixes a whole class of problem may count where a large mechanical change does not. If you believe your contribution crosses that line and it has not been reflected, say so in an issue — being asked is better than being resented.

Where a contribution is adapted from someone else's work rather than written from scratch, credit it **in the docstring of the code itself** (an "original author" line), so the attribution travels with the code rather than living only in a file nobody reads.

### Reporting Bugs

<!-- omit in toc -->
#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to collect information and describe the issue in detail in your report. Please complete the following steps in advance to help us fix any potential bug as fast as possible.

- Make sure that you are using the latest version.
- Determine if your bug is really a bug and not an error on your side e.g. using incompatible environment components/versions (Make sure that you have read the [documentation](https://amoccommunity.github.io/AMOCatlas/). If you are looking for support, you might want to check [this section](#i-have-a-question)).
- Collect information about the bug:
- Stack trace (Traceback) or screenshot error message
- OS, Platform and Version (Windows, Linux, macOS, x86, ARM)
- Version of the interpreter, compiler, SDK, runtime environment, package manager, depending on what seems relevant.
- Possibly your input and the output

<!-- omit in toc -->
#### How Do I Submit a Good Bug Report?

> You must never report security related issues, vulnerabilities or bugs including sensitive information to the issue tracker, or elsewhere in public. Instead sensitive bugs must be sent by email to [mailto:eleanorfrajka@gmail.com](eleanorfrajka@gmail.com).
<!-- You may add a PGP key to allow the messages to be sent encrypted as well. -->

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/AMOCcommunity/amocatlas/issues/new).
- Explain the behavior you would expect and the actual behavior.
- Please provide as much context as possible and describe the *reproduction steps* that someone else can follow to recreate the issue on their own. This usually includes your code. For good bug reports you should isolate the problem and create a reduced test case.
- Provide the information you collected in the previous section.

Once it's filed:

- The project team will label the issue accordingly.
- A team member will try to reproduce the issue with your provided steps. If there are no reproduction steps or no obvious way to reproduce the issue, the team will ask you for those steps and mark the issue as `needs-repro`. Bugs with the `needs-repro` tag will not be addressed until they are reproduced.
- If the team is able to reproduce the issue, it will be marked `needs-fix`, as well as possibly other tags (such as `critical`), and the issue will be left to be [implemented by someone](#your-first-code-contribution).

<!-- You might want to create an issue template for bugs and errors that can be used as a guide and that defines the structure of the information to be included. If you do so, reference it here in the description. -->


### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for amocatlas, **including completely new features and minor improvements to existing functionality**. Following these guidelines will help maintainers and the community to understand your suggestion and find related suggestions.

<!-- omit in toc -->
#### Before Submitting an Enhancement

- Make sure that you are using the latest version.
- Read the [documentation](https://amoccommunity.github.io/AMOCatlas/) carefully and find out if the functionality is already covered, maybe by an individual configuration.
- Perform a [search](https://github.com/AMOCcommunity/amocatlas/issues) to see if the enhancement has already been suggested. If it has, add a comment to the existing issue instead of opening a new one.
- Find out whether your idea fits with the scope and aims of the project.  Keep in mind that we want features that will be useful to the majority of our users and not just a small subset.

<!-- omit in toc -->
#### How Do I Submit a Good Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://github.com/AMOCcommunity/amocatlas/issues).

- Use a **clear and descriptive title** for the issue to identify the suggestion.
- Provide a **step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why. At this point you can also tell which alternatives do not work for you.
- You may want to **include screenshots** which help you demonstrate the steps or point out the part which the suggestion is related to.
- **Explain why this enhancement would be useful** to most amocatlas users. You may also want to point out the other projects that solved it better and which could serve as inspiration.

<!-- You might want to create an issue template for enhancement suggestions that can be used as a guide and that defines the structure of the information to be included. If you do so, reference it here in the description. -->

### Your First Code Contribution

Getting started adding your own functionality.

#### amocatlas organisation

Code is organised into files within `amocatlas/*.py` and demonstrated in jupyter notebooks in `notebooks/*.ipynb`.  The *.py* files include mostly functions (with their necessary packages imported) while the notebooks call these functions and display the plots generated.

The *.py* files are separated into broad categories of readers (to load datesets), plotters (to plot or show data), standardise (to apply some common formatting or metadata), tools and utilities.  If you'd like to add a function to calculate something and then to plot the result of the calculation, then you would write a function in `tools.py` to do the calculation, and the plotting function in `plotters.py`.  There are a couple exceptions: if it's a *very* simple calculation (mean, median, difference between two quantities), then you might include this calculation within the plotting function.  Or if the calculation is more complicated but easily displayed with an existing function, then you might have a calculation function `tools.calc_foo_bar()` and then use an existing plotting function to display it.

#### Best practices for new functions

- Once you've added a function, you can test it against one of the sample datasets in `notebooks/demo.ipynb`. Does it have the same behaviour on those sample datasets as you expect?
- Have you followed the conventions for naming your function? Generally, function names should be short, agnostic about the array data used, and understandable to Person X. We also loosely follow naming conventions to help the new user understand what a function might do (e.g., plotting functions in `plotter.py` typically start with the name `plot_blahblah()` while calculations are `calc_blahblah()` and calculations with special outputs are `compute_blahblah()`. Functions not intended for use by the end user (e.g. sub-calculations) should be added to `utilities.py`
- Unless otherwise required, we suggest to pass an xarray dataset (as you get from loading an array dataset) as the input. There are some parameters that can be additionally passed to carry out subsets on the data or select the variable of interest.
- Did you write a docstring? We use the [numpy standard for docstings](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard). We also suggest including your name or GitHub handle under the original author heading. Look at some existing docstrings in `amocatlas` if you are unsure of the format.
- There are also some basic error checking behaviours you should consider including. If you're plotting a particular variable, use the `amocatlas.utilities._check_necessary_variables()` function to check whether or not the required variables are within the dataset passed to the function.
- For plotting functions on a single axis, you should include as optional inputs the `fig` and `ax`, and return the same, to enable their usage within multi-axes plots. For plotting functions with multiple or interrelated axes, perhaps fig and ax shouldn't be included as inputs, but can be provided as outputs for the user to make onward edits.
- For plotting, keep figures visually consistent with the existing ones: reuse the line widths, figure sizes, and font sizes already used in `plotters.py` rather than introducing new magic values scattered through the code.
- Each new function should have a corresponding test, feel free to ask if you're not sure how to write a test!

### Metadata, provenance, and pull-request hygiene

amocatlas creates no science data — its product is *metadata*: the same numbers as the upstream publications, re-served with correct attribution, vocabulary, units, and provenance. A few conventions follow directly from that:

- **Never silently substitute a default** where the correct value cannot be determined. Leave it empty, or raise / warn loudly and record what was assumed. A plausible wrong value (a mangled contributor name, a dropped EDMO code, a wrong-hemisphere latitude) is worse than a missing one, because nothing downstream can detect it.
- **Preserve upstream qualifiers and units exactly.** Units are not optional; never strip or assume them.
- **Record provenance.** When a processing step applies a correction, threshold, or registry replacement, make it inspectable — prefer a `warnings.warn` a user will see in a notebook over a DEBUG log they never read, and where relevant record what was applied in the output's attributes.
- **One logical change per pull request.** A rename PR that also fixes a bug, or a fix that also carries an unrelated feature, is a PR nobody can review cleanly. If two changes are independent, split them.
- **Tests should assert a value, not that something ran.** For anything numerical, assert against a figure you can justify independently of the code. Avoid tests that pass when nothing happened — `assert result is not None` on a function that returns `None` on failure is the shape to avoid.

### Jupyter Notebook Guidelines

When working with notebooks in this repository:

- **Clear outputs before committing**: Generally, clear all notebook outputs before committing to keep the repository clean
- **Exception**: `amoc_paperfigs.ipynb` should **keep its outputs** because:
  - It requires PyGMT/GMT which are not available in CI
  - The outputs show publication-quality figures that can't be regenerated automatically
  - This notebook is copied (not executed) during documentation builds

All other notebooks (`demo.ipynb`, etc.) should have their outputs cleared before committing.

### Improving The Documentation

Our [documentation](https://amoccommunity.github.io/AMOCatlas/) is built from the function docstrings and the [example notebook](https://amoccommunity.github.io/AMOCatlas/demo-output.html). If you think the documentation could be better, do not hesitate to suggest an improvement! Either in an Issue or a PR.

To build the documentation locally you need to install a few extra requirements:

- Install `make` for your computer, e.g. on ubuntu with `sudo apt install make`
- Install `pandoc` (nbsphinx renders the notebooks through it), e.g. on ubuntu with `sudo apt install pandoc`, or from conda-forge
- Install the documentation extras. Activate the environment you use for amocatlas, navigate to the top directory of this repo, then run `pip install -e ".[docs]"`

Once you have the extras installed, you can build the docs locally by navigating to the `docs/` directory and running `make clean html`. This command will create a directory called `build/` which contains the html files of the documentation. Open the file `docs/build/html/index.html` in your browser, and you will see the docs with your changes applied. After making more changes, just run make clean html again to rebuild the docs.

<!-- omit in toc -->
## Attribution
This guide is based on the **contributing-gen**. [Make your own](https://github.com/bttger/contributing-gen)!
