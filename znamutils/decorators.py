from decorator import decorator
from znamutils import slurm_helper
import inspect
from inspect import signature, Parameter
from decopatch import function_decorator, DECORATED
from makefun import wraps, add_signature_parameters
from inspect import signature, Parameter
from pathlib import Path


@function_decorator
def slurm_it(
    func=DECORATED,
    *,
    conda_env=None,
    module_list=None,
    slurm_options=None,
    imports=None,
    from_imports=None,
    print_job_id=False,
):
    """
    Decorator to run a function on slurm.

    Running the decorated function with use_slurm=False will run the function and return
    its normal output.
    Running the decorated function with use_slurm=True will create a slurm script and
    a python script, submit the slurm script and return the job id of the slurm job.

    The decorated function will have 6 new keyword arguments:
        use_slurm (bool): whether to use slurm or not
        dependency_type (str, optional): Type of dependence on previous jobs.
            Defaults to "afterok" which only runs the next job if all previous
            jobs have finished successfully. Other options are "after", "afterany",
            "aftercorr" and "afternotok". See sbatch documentation for more details.
        job_dependency (str): job id to depend on
        slurm_folder (str): where to write the slurm script and logs
        scripts_name (str): name of the slurm script and python file
        slurm_options (dict): options to pass to sbatch

    The default slurm options are:
        ntasks=1
        time="12:00:00"
        mem="32G"
        partition="cpu"

    Args:
        func (function): function to decorate
        conda_env (str): name of the conda environment to activate. Required.
        module_list (list, optional): list of modules to load with ml. Defaults to None.
        slurm_options (dict, optional): options to pass to sbatch. Will be used to
            update the default config (see above) if not None. Defaults to None.
        imports (str or list, optional): List of imports to add to the script. Defaults
            to None.
        from_imports (dict, optional): Dictionary of imports to add to the python
            script. Keys are the module names, values are the functions to import. For
            instance {'numpy': 'mean'} results in `from numpy import mean`. If `None`,
            the decorated function will be imported from its parent module. Defaults to
            None.
        print_job_id (bool, optional): Whether to print the job id of the slurm job in
            the log file. Defaults to False.

    Returns:
        function: decorated function
    """
    # make a copy of default slurm options to avoid modifying the original
    if slurm_options is None:
        slurm_options = {}
    default_slurm_options = slurm_options.copy()

    # add parameters to the wrapped function signature
    func_sig = signature(func)
    new_parameter_names = [
        "use_slurm",
        "dependency_type",
        "job_dependency",
        "slurm_folder",
        "scripts_name",
        "slurm_options",
        "batch_param_names",
        "batch_param_list",
    ]
    parameters = []
    for name in new_parameter_names:
        default = False if name == "use_slurm" else None
        parameters.append(
            Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, default=default)
        )
    new_sig = add_signature_parameters(
        func_sig,
        last=parameters,
    )
    from_imports = from_imports or {func.__module__: func.__name__}

    # create the new function with modified signature
    @wraps(func, new_sig=new_sig)
    def new_func(*args, **kwargs):
        # pop the slurm only arguments
        use_slurm = kwargs.pop("use_slurm")
        dependency_type = kwargs.pop("dependency_type")
        job_dependency = kwargs.pop("job_dependency")
        slurm_folder = kwargs.pop("slurm_folder")
        scripts_name = kwargs.pop("scripts_name")
        slurm_options = kwargs.pop("slurm_options")
        batch_param_list = kwargs.pop("batch_param_list")
        batch_param_names = kwargs.pop("batch_param_names")

        if slurm_options is None:
            slurm_options = {}
        slurm_options = dict(default_slurm_options, **slurm_options)

        if isinstance(job_dependency, list) or isinstance(job_dependency, tuple):
            job_dependency = ":".join(job_dependency)

        if not use_slurm:
            if job_dependency is not None:
                raise ValueError("job_dependency should be None if use_slurm is False")
            return func(*args, **kwargs)

        if slurm_folder is None:
            raise ValueError("slurm_folder should be provided if use_slurm is True")

        # create the slurm scripts
        if scripts_name is None:
            scripts_name = func.__name__
        slurm_folder = Path(slurm_folder)
        assert slurm_folder.exists(), f"Folder {slurm_folder} does not exist"
        python_file = slurm_folder / f"{scripts_name}.py"
        sbatch_file = slurm_folder / f"{scripts_name}.sh"
        assert conda_env is not None, "conda_env should be provided in the decorator"

        if batch_param_names is not None:
            if isinstance(batch_param_names, str):
                batch_param_names = [batch_param_names]

            assert batch_param_list is not None, "batch_param_list should be provided"
            n_params = len(batch_param_names)
            for l in batch_param_list:
                assert (
                    len(l) == n_params
                ), "All lists in batch_param_list should have the same length"
            env_vars_to_pass = {p: p for p in batch_param_names}
        else:
            env_vars_to_pass = None
        slurm_helper.create_slurm_sbatch(
            target_folder=slurm_folder,
            script_name=sbatch_file.name,
            python_script=str(python_file),
            conda_env=conda_env,
            slurm_options=slurm_options,
            module_list=module_list,
            print_job_id=print_job_id,
            env_vars_to_pass=env_vars_to_pass,
        )

        # make sure that the function does not use slurm once running on slurm
        kwargs["use_slurm"] = False
        if batch_param_names is not None:
            # remove from kwargs the parameters that will be provided by batch
            for p_name in batch_param_names:
                v = kwargs.pop(p_name, None)
                if v is not None:
                    print(f"Warning: parameter {p_name}={v} was removed from kwargs")
                    print("It will be passed as environment variable")

        slurm_helper.python_script_single_func(
            target_file=python_file,
            function_name=func.__name__,
            arguments=kwargs,
            imports=imports,
            from_imports=from_imports,
            vars2parse=env_vars_to_pass,
        )

        if dependency_type is None:
            dependency_type = "afterok"

        if env_vars_to_pass is not None:
            # run multiple jobs
            job_ids = []
            for params in batch_param_list:
                env_vars = {k: v for k, v in zip(batch_param_names, params)}
                jid = slurm_helper.run_slurm_batch(
                    sbatch_file,
                    dependency_type=dependency_type,
                    job_dependency=job_dependency,
                    env_vars=env_vars,
                )
                job_ids.append(jid)
            return job_ids

        return slurm_helper.run_slurm_batch(
            sbatch_file,
            dependency_type=dependency_type,
            job_dependency=job_dependency,
        )

    # return the new function
    return new_func
