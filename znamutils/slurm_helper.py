"""Function to help to generate and run slurm scripts"""
import shlex
import subprocess
from pathlib import Path


def run_slurm_batch(
    script_path,
    dependency_type="afterok",
    job_dependency=None,
    env_vars=None,
    dry_run=False,
):
    """Run a slurm script

    Args:
        script_path (str): Full path to the script
        dependency_type (str, optional): Type of dependence on previous jobs.
            Defaults to "afterok" which only runs the next job if all previous
            jobs have finished successfully. Other options are "after", "afterany",
            "aftercorr" and "afternotok". See sbatch documentation for more details.
        job_dependency (str, optional): Job ID that needs to finish before running
            sbtach. Defaults to None.
        env_vars (dict, optional): Dictionary of environment variables to pass to the
            script. Defaults to None.
        dry_run (bool, optional): Whether to run the command or just print it.

    Returns:
        str: Job ID of the sbatch job
    """
    if job_dependency is not None:
        dep = f"--dependency={dependency_type}:{job_dependency} "
    else:
        dep = ""

    if env_vars is not None:
        vars = "--export="
        vars += ",".join([f"{k}={v}" for k, v in env_vars.items()])
        vars += " "
    else:
        vars = ""

    command = f"sbatch {vars}{dep}{script_path}"

    if dry_run:
        print(command)
        return command

    procout = subprocess.check_output(shlex.split(command))
    # get the job id
    job_id = procout.decode("utf-8").split(" ")[-1].strip()
    return job_id


def create_slurm_sbatch(
    target_folder,
    script_name,
    python_script,
    conda_env,
    slurm_options=None,
    module_list=None,
    split_err_out=False,
    print_job_id=True,
    add_jobid_to_output=False,
    env_vars_to_pass=None,
):
    """Create a slurm sh script that will call a python script

    Args:
        target_folder (str): Where to write the script?
        script_name (str): Name of the script
        python_script (str): Path to the python script
        conda_env (str): Name of the conda environment to load
        slurm_options (dict, optional): Options to give to sbatch. Defaults to None.
        module_list (list, optional): List of modules to load before calling the python
            script. Defaults to None.
        split_err_out (bool, optional): Whether to split the error and output files.
            Defaults to True.
        print_job_id (bool, optional): Whether to print the job id in the log file.
            Defaults to True.
        add_jobid_to_output (bool, optional): Whether to add the job id to the output
            file. Required when env_vars_to_pass is not None. Defaults to False.
        env_vars_to_pass (dict, optional): Dictionary of environment variables to pass
            to the script. Keys are the name of the argument expected by the python
            script and values are the environment variable. Defaults to None.
    """
    if not script_name.endswith(".sh"):
        script_name += ".sh"
    if env_vars_to_pass is None:
        env_vars_to_pass = {}

    target_folder = Path(target_folder)
    default_options = dict(
        ntasks=1,
        time="12:00:00",
        mem="32G",
        partition="ncpu",
        output=str(target_folder / script_name.replace(".sh", ".out")),
    )
    if add_jobid_to_output or env_vars_to_pass:
        default_options["output"] = default_options["output"].replace(".out", "_%j.out")

    if split_err_out:
        default_options["error"] = default_options["output"].replace(".out", ".err")

    if slurm_options is None:
        slurm_options = {}

    slurm_options = dict(default_options, **slurm_options)

    with open(target_folder / script_name, "w") as fhandle:
        fhandle.write("#!/bin/bash\n")
        options = "\n".join([f"#SBATCH --{k}={v}" for k, v in slurm_options.items()])
        fhandle.writelines(options)
        # add some boilerplate code
        if module_list is not None:
            boiler = "\n" + "\n".join([f"ml {module}" for module in module_list]) + "\n"
        else:
            boiler = "\n"

        if print_job_id:
            boiler += 'echo "Job ID: $SLURM_JOB_ID"\n'

        LD_PATH = f"~/.conda/envs/{conda_env}/lib/"
        boiler += "\n".join(
            [
                "source ~/.bashrc ",
                f"conda activate {conda_env}",
                f"export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{LD_PATH}",
                "",
            ]
        )
        fhandle.write(boiler)

        cmd = f"python {python_script}"
        if env_vars_to_pass:
            for k, v in env_vars_to_pass.items():
                if not k.startswith("--"):
                    k = "--" + k
                elif k.startswith("-"):
                    raise ValueError(f"Short options are not supported: {k}")
                cmd += f" {k} ${v}"
        # and the real call
        fhandle.write(f"\n\n{cmd}\n")


def python_script_single_func(
    target_file,
    function_name,
    arguments=None,
    vars2parse=None,
    imports=None,
    from_imports=None,
    path2string=True,
):
    """Create a python script that will call a function

    Args:
        target_file (str): Where to write the script?
        function_name (str): Name of the function to call
        arguments (dict, optional): Dictionary of arguments to pass to the function.
            Defaults to None.
        vars2parse (dict, optional): Dictionary of variables to parse from the command
            line. Keys are the keyword arguments for the python function and values the
            cli variable to parse. Defaults to None.
        imports (str or list, optional): List of imports to add to the script. Defaults
            to None.
        from_imports (dict, optional): Dictionary of imports to add to the script. Keys
            are the module names, values are the functions to import. For instance
            {'numpy': 'mean'} results in `from numpy import mean`. Defaults to None.
        path2string (bool, optional): Whether to convert arguments that are paths to
            strings. Defaults to True.
    """

    target_file = Path(target_file)
    assert target_file.parent.exists(), f"{target_file.parent} does not exist"

    if vars2parse is None:
        vars2parse = {}

    if imports is None:
        imports = []
    elif isinstance(imports, str):
        imports = [imports]

    if vars2parse and ("argparse" not in imports):
        imports.append("argparse")

    with open(target_file, "w") as fhandle:
        for imp in imports:
            fhandle.write(f"import {imp}\n")
        fhandle.write("\n")
        if from_imports is not None:
            for module, function in from_imports.items():
                fhandle.write(f"from {module} import {function}\n")
            fhandle.write("\n")
        if vars2parse:
            fhandle.write("parser = argparse.ArgumentParser()\n")
            for k, v in vars2parse.items():
                fhandle.write(f"parser.add_argument('--{v}')\n")
            fhandle.write("args = parser.parse_args()\n")
            fhandle.write("\n")

        fhandle.write(f"{function_name}(")
        if arguments is not None:
            for k, v in arguments.items():
                if path2string and isinstance(v, Path):
                    v = str(v)
                fhandle.write(f"{k}={repr(v)}, ")
        if vars2parse:
            for k, v in vars2parse.items():
                fhandle.write(f"{k}=args.{v}, ")
        fhandle.write(")\n")


def python_script_from_template(
    target_folder, source_script, target_script_name=None, arguments=None
):
    """Create a python script from a template

    Arguments in the template should be of the form XXX_ARGUMENT_XXX. They will be
    replaced by the value of `arguments["ARGUMENT"]`

    Args:
        target_folder (str): Where to write the script?
        source_script (str): Path to the template script
        target_script_name (str, optional): Name of the target script if different from
            source_script. Defaults to None.
        arguments (dict, optional): Dictionary of arguments to replace in the template.
            Defaults to None.
    """
    source_script = Path(source_script)
    if arguments is None:
        arguments = {}
    source = source_script.read_text()
    for k, v in arguments.items():
        source = source.replace(f'"XXX_{k.upper()}_XXX"', repr(v))
    if target_script_name is None:
        target_script_name = source_script.name
    python_script = Path(target_folder) / target_script_name
    with open(python_script, "w") as fhandle:
        fhandle.write(source)
