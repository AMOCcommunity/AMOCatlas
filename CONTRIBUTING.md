<!-- omit in toc -->
# Contributing to amocatlas

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them.


<!-- omit in toc -->
## Table of Contents

- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)
- [Your First Code Contribution](#your-first-code-contribution)
- [Improving The Documentation](#improving-the-documentation)
- [Styleguides](#styleguides)
- [Commit Messages](#commit-messages)
- [Join The Project Team](#join-the-project-team)



## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://amoccommunity.github.io/amocatlas/).

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

> ### Legal Notice <!-- omit in toc -->
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project licence.

### Reporting Bugs

<!-- omit in toc -->
#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to collect information and describe the issue in detail in your report. Please complete the following steps in advance to help us fix any potential bug as fast as possible.

- Make sure that you are using the latest version.
- Determine if your bug is really a bug and not an error on your side e.g. using incompatible environment components/versions (Make sure that you have read the [documentation](https://amoccommunity.github.io/amocatlas/). If you are looking for support, you might want to check [this section](#i-have-a-question)).
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
- Read the [documentation](https://amoccommunity.github.io/amocatlas/) carefully and find out if the functionality is already covered, maybe by an individual configuration.
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
- For plotting, see the guidance on uniformity (using standard lineswidths, figure sizes and font sizes etc.). These are all described in `amocatlas/amocatlas.mplstyle`, in case an individual user wants to change these to their preferences.
- Each new function should have a corresponding test, feel free to ask if you're not sure how to write a test!

### Improving The Documentation

Our [documentation](https://amoccommunity.github.io/amocatlas/) is built from the function docstrings and the [example notebook](https://amoccommunity.github.io/amocatlas/demo-output.html). If you think the documentation could be better, do not hesitate to suggest an improvement! Either in an Issue or a PR.

To build the documentation locally you need to install a few extra requirements:

- Install `make` for your computer, e.g. on ubuntu with `sudo apt install make`
- Install the additional python requirements. Activate the environment you use for working with glidertest, navigate to the top directory of this repo, then run `pip install -r requirements-dev.txt`

Once you have the extras installed, you can build the docs locally by navigating to the `docs/` directory and running `make clean html`. This command will create a directory called `build/` which contains the html files of the documentation. Open the file `docs/build/html/index.html` in your browser, and you will see the docs with your changes applied. After making more changes, just run make clean html again to rebuild the docs.

<!-- omit in toc -->
## Attribution
This guide is based on the **contributing-gen**. [Make your own](https://github.com/bttger/contributing-gen)!
