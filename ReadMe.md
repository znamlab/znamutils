# ZnamUtils

This package contains common utilities for Znamenskiy's lab projects. It should remain
as lightweight as possible and independant of flexiznam.

# SlurmIt

`@slurmit` is a decorator allowing to run a function on slurm. Once set up, running the 
decorated function with use_slurm=False will run the function and return its normal output.
Running the decorated function with use_slurm=True will create a slurm script and a python 
script, submit the slurm script and return the job id of the slurm job.

## Usage

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

The decorator has three arguments:
- conda_env (str): name of the conda environment to activate. Required.
- module_list (list, optional): list of modules to load with ml. Defaults to None.
- slurm_options (dict, optional): options to pass to sbatch. Will be used to
    update the default config (see below) if not None. Defaults to None.

The default parameters of SlurmIt are: 
```
ntasks=1
time="12:00:00"
mem="32G"
partition="cpu"
```

An example of fully custromised decoration would be:

```python
@slurm_it(conda_env='myenv', module_list=['FFmpeg', 'cuda'], slurm_options=dict(partition="gpu")
def analysis_step(param1, param2):
  out = dostuff(param1, param2)
  return out
```

## Calling the decorated function

The decorated function will have 4 new keyword arguments:

```
use_slurm (bool): whether to use slurm or not
job_dependency (str): job id to depend on
slurm_folder (str): where to write the slurm script and logs
scripts_name (str): name of the slurm script and python file
```

When `use_slurm = True`, `slurm_folder` must be provided. 
If `scripts_name` is false, the name of the function is used instead.

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

IMPORT and paramter types (to document)

# Slurm utils

A collection of utilities to interact with the Slurm scheduler. Used by `slurmit`

# Tests

To run the test, we need to access camp/nemo and slurm. It also requires a flexiznam installation.

