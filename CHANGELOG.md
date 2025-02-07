
## Changelog

### [v0.10] - 2024-10-09

Minor changes:

- Change boiler code to source `.bashrc` to find conda environment (instead of
  `ml` and `activate base`). This requires `conda init` to be run beforehand.
- Packaging: switch to `pyproject.toml` for packaging.

### [v0.9] - 2024-06-06

- Bugfix: slurm_it runs if dependency is an empty list.

### [v0.8] - 2024-05-31

- Feature: Option to run batch jobs in parallel slurm jobs. If `batch_param_names` and
`batch_param_values` are provided, the function will be called for each tuple of values
in `batch_param_values`


### [v0.7] - 2024-05-14

- Feature: `pathlib.Path` are automatically converted to strings in the main slurm
    python script. This avoid crashing because `PosixPath` and co are not imported.

### [v0.6] - 2024-04-04

- Change default cpu partition to `ncpu`

### [v0.5] - 2024-03-27

- Option to print job ID in log when starting.


### [v0.4] - 2024-01-17

- Job dependencies that are list or tuples are automatically formatted as `afterok:jobid1:jobid2:...`

### [v0.3] - 2023-12-05

- Bugfix: `slurm_options` was required but can now be ommited in the decorator

### [v0.2] - 2023-12-05

- Add option to change slurm options when calling the decorated function

### [v0.1] - 2023-08-13

- Initial release
