
## Changelog

### [v0.3] - 2024-01-17

- Job dependencies that are list or tuples are automatically formatted as `afterok:jobid1:jobid2:...`
- Bugfix: `slurm_options` was required but can now be ommited in the decorator

### [v0.2] - 2023-12-05

- Add option to change slurm options when calling the decorated function

### [v0.1] - 2023-08-13

- Initial release
