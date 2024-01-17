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
    conda_env=None,
    module_list=None,
    slurm_options=None,
    imports=None,
    from_imports=None,
):
    """
    Decorator to run a function on slurm.

    Running the decorated function with use_slurm=False will run the function and return
    its normal output.
    Running the decorated function with use_slurm=True will create a slurm script and
    a python script, submit the slurm script and return the job id of the slurm job.

    The decorated function will have 4 new keyword arguments:
        use_slurm (bool): whether to use slurm or not
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

    Returns:
        function: decorated function
    """
    # make a copy of default slurm options to avoid modifying the original
    if slurm_options is None:
        slurm_options = {}
    default_slurm_options = slurm_options.copy()

    # add parameters to the wrapped function signature
    func_sig = signature(func)
    use_slurm = Parameter(
        "use_slurm", kind=Parameter.POSITIONAL_OR_KEYWORD, default=False
    )
    job_dependency = Parameter(
        "job_dependency", kind=Parameter.POSITIONAL_OR_KEYWORD, default=None
    )
    slurm_folder = Parameter(
        "slurm_folder", kind=Parameter.POSITIONAL_OR_KEYWORD, default=None
    )
    script_name = Parameter(
        "scripts_name", kind=Parameter.POSITIONAL_OR_KEYWORD, default=None
    )
    slurm_options = Parameter(
        "slurm_options", kind=Parameter.POSITIONAL_OR_KEYWORD, default=None
    )

    new_sig = add_signature_parameters(
        func_sig,
        last=(use_slurm, job_dependency, slurm_folder, script_name, slurm_options),
    )
    from_imports = from_imports or {func.__module__: func.__name__}
    # create the new function with modified signature
    @wraps(func, new_sig=new_sig)
    def new_func(*args, **kwargs):

        # pop the slurm only arguments
        use_slurm = kwargs.pop("use_slurm")
        job_dependency = kwargs.pop("job_dependency")
        slurm_folder = kwargs.pop("slurm_folder")
        scripts_name = kwargs.pop("scripts_name")
        slurm_options = kwargs.pop("slurm_options")
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

        slurm_helper.create_slurm_sbatch(
            target_folder=slurm_folder,
            script_name=sbatch_file.name,
            python_script=str(python_file),
            conda_env=conda_env,
            slurm_options=slurm_options,
            module_list=module_list,
        )

        # make sure that the function does not use slurm once running on slurm
        kwargs["use_slurm"] = False
        slurm_helper.python_script_single_func(
            target_file=python_file,
            function_name=func.__name__,
            arguments=kwargs,
            imports=imports,
            from_imports=from_imports,
        )

        return slurm_helper.run_slurm_batch(sbatch_file, job_dependency=job_dependency)

    # return the new function
    return new_func
