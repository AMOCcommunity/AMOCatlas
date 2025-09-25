# Installation

To install the latest released version of this package from PyPI, use
```sh
python -m pip install amocatlas
```
This allows you to import the package into a python file or notebook with:
```python
import amocatlas
```
### Install for contributing

Or, to install a local, development version of amocatlas, clone the repository, open a terminal in the root directory (next to this readme file) and run these commands:

```sh
git clone https://github.com/AMOCcommunity/amocatlas.git
cd amocatlas
pip install -r requirements-dev.txt
pip install -e .
```
This installs amocatlas locally.  The `-e` ensures that any edits you make in the files will be picked up by scripts that import functions from glidertest.  The `requirements-dev.txt` includes more python packages which are needed for development, including to build this documentation page, run tests, or run linting (formatting checks on your code).

You can run the example jupyter notebook by launching jupyterlab with `jupyter-lab` and navigating to the `notebooks` directory, or in VS Code or another python GUI.

All new functions should include tests.  You can run tests locally and generate a coverage report with:
```sh
pytest --cov=amocatlas --cov-report term-missing tests/
```
This tells you what lines of a module (e.g., `amocatlas/readers.py`) are not run through during the existing tests (located in `tests/`).

Try to ensure that all the lines of your contribution are covered in the tests.

See also the [Developers Guide](developer_guide.md) for coding conventions used here (e.g., style of comments at the top of a function), the automatic "GitHub Actions" which are triggered when you make a pull request,  and an example workflow to use Git to collaborate on code.
