FAQ / Troubleshooting
======================


#### I get an error when doing `from amocatlas import plotters`

This is because your code can't find the project `amocatlas`.

**Option 1:** Install the package `amocatlas` locally

Activate your environment.

```
source venv/bin/activate
```

then install your project from the terminal window in, e.g., `/a/path/on/your/computer/amocatlas` as
```
pip install -e .
```
This will set it up so that you are installing the package in "editable" mode.  Then any changes you make to the scripts will be taken into account (though you may need to restart your kernel).

**Option 2:** Add the path to the `amocatlas` to the code

Alternatively, you could add to your notebook some lines so that your code can "find" the package.  This might look like
```
import sys
sys.path.append('/a/path/on/your/computer/amocatlas')
```
before the line where you try `from amocatlas import plotters`.

#### Failing to install the package in a Github Action

```
× Getting requirements to build editable did not run successfully.
│ exit code: 1
╰─> See above for output.
```

To test the installation, you'll want a fresh environment.

**In a terminal window, at the root of your project** (for me, this is `/a/path/on/your/computer/amocatlas/`), run the following commands in order.
```
virtualenv venv
source venv/bin/activate && micromamba deactivate
pip install -r requirements.txt
pip install -e .
```

Then check and troubleshoot any errors.  When this runs, you are probably ready to try it with the GitHub Actions (where the workflows are in your repository in `.github/workflows/*.yml`)

