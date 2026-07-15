# ZnamUtils

This package contains common utilities for Znamenskiy's lab projects.

# SlurmIt

`@slurm_it` is a decorator allowing to run a function on slurm. Once set up, running the
decorated function with `use_slurm=False` will run the function and return its normal output.
Running the decorated function with `use_slurm=True` will create a slurm script and a python
script, submit the slurm script and return the job id of the slurm job.

## Usage

If we want to run this function on slurm:

```python
def analysis_step(param1, param2):
  out = dostuff(param1, param2)
  return out
```

We need to decorate it

```python
@slurm_it(conda_env='myenv')
def analysis_step(param1, param2):
  out = dostuff(param1, param2)
  return out
```

Then it can be called normally:

```python
analysis_step(param1, param2, use_slurm=False)
```

Or on slurm:

```python
analysis_step(param1, param2, use_slurm=True, slurm_folder='~/somewhere')
```

## Setting slurm parameters

The decorator has five arguments:
- conda_env (str): name of the conda environment to activate. Required.
- module_list (list, optional): list of modules to load with ml. Defaults to None.
- slurm_options (dict, optional): options to pass to sbatch. Will be used to
    update the default config (see below) if not None. Defaults to None.
- imports (list, optional): list of imports to add to the python script. Defaults to None.
- from_imports (dict, optional): dict of imports to add to the python script as "from
    key import value". Defaults to None.

The default parameters of SlurmIt are:
```
ntasks=1
time="12:00:00"
mem="32G"
partition="cpu"
```

An example of fully custromised decoration would be:

```python
@slurm_it(conda_env='myenv',
  module_list=['FFmpeg', 'cuda'],
  slurm_options=dict(partition="gpu",
  imports=['numpy', 'matplotlib'],
  from_imports={'sklearn': 'svm'}
  )
def analysis_step(param1, param2):
  out = dostuff(param1, param2)
  return out
```

> Note:
> `imports` and `from_imports` are useful only if the decorated function require non
> built-in datatype arguments or if the module containing the function cannot be
> accessed from the python script in the same way as it is in the code calling slurm_it
> (for instance if you use relative imports). Then explicitely setting `from_imports` to
> import the decorated function is required.

## Calling the decorated function

The decorated function will have 6 new keyword arguments:

```
use_slurm (bool): whether to use slurm or not
dependency_type (str, optional): Type of dependence on previous jobs.
    Defaults to "afterok" which only runs the next job if all previous
    jobs have finished successfully. Other options are "after", "afterany",
    "aftercorr" and "afternotok". See sbatch documentation for more details.
job_dependency (str): job id to depend on
slurm_folder (str): where to write the slurm script and logs
scripts_name (str): name of the slurm script and python file
slurm_options (dict): options to pass to sbatch, will update the default options
  provided in the decorator.
batch_param_names (list): list of parameters on which the function should be batched
batch_param_values (list): list of values for the batched parameters
```

When `use_slurm = True`, `slurm_folder` must be provided.
If `scripts_name` is false, the name of the function is used instead.

If `batch_param_names` is provided, `batch_param_values` must be a list of tuples the
same length as `batch_param_names`. The function will be called for each tuple of
values in `batch_param_values`.

Calling:

```python
jobid = analysis_step(param1, param2, use_slurm=True, slurm_folder='~/somewhere', job_depency=1234324)
```
will create `~/somewhere/analysis_step.py` and `~/somewhere/analysis_step.sh`, then `sbatch` the `sh` script
with `--dependency=afterok:1234324`.

```python
jobid = analysis_step(param1, param2, use_slurm=True, slurm_folder='~/somewhere', scripts_name='run_2')
```

will create `~/somewhere/run2.py` and `~/somewhere/run2.sh`, then `sbatch` the `sh` script without
dependencies.


## Limitations:

IMPORT and parameter types (to document)

# Slurm utils

A collection of utilities to interact with the Slurm scheduler. Used by `slurmit`

# Tests

To run the test, we need to access camp/nemo and slurm. It also requires a flexiznam installation.

# Development

This project uses [uv](https://docs.astral.sh/uv/) to manage the dev environment.

Set up a local environment:

```bash
uv venv
uv pip install -e ".[dev]"
source .venv/bin/activate
```

Run the checks:

```bash
pytest
ruff check .
ruff format .
```

`pre-commit` hooks (ruff, mypy, etc.) run automatically via [pre-commit.ci](https://pre-commit.ci/) on
pull requests. To run them locally:

```bash
pre-commit run --all-files
```

> Note: this repo does not commit a `uv.lock` file. znamutils is a library, not an
> application: a lock file pins exact dependency versions for reproducibility, which
> matters for something you deploy, but not for a library that gets installed
> alongside a consumer's own dependency tree. Testing against current, unpinned
> dependency versions (as CI does) is more likely to catch real compatibility issues
> than testing against a frozen snapshot. For this reason, prefer the `uv venv` /
> `uv pip install` workflow above over `uv run`, which operates in "project mode" and
> will auto-create a `uv.lock` as a side effect.
