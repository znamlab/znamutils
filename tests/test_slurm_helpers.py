from pathlib import Path
from znamutils import slurm_helper

try:
    import flexiznam as flz
except ImportError:
    raise ImportError("flexiznam is required to run this test")


def test_create_slurm_sbatch(tmpdir):
    slurm_helper.create_slurm_sbatch(
        tmpdir,
        print_job_id=True,
        conda_env="cottage_analysis",
        python_script="test.py",
        script_name="test.sh",
    )
    with open(tmpdir / "test.sh") as f:
        txt = f.read()
    lines = [
        "#!/bin/bash",
        "#SBATCH --ntasks=1",
        "#SBATCH --time=12:00:00",
        "#SBATCH --mem=32G",
        "#SBATCH --partition=ncpu",
        f"#SBATCH --output={tmpdir}/test.out",
        'echo "Job ID: $SLURM_JOB_ID"',
        "ml Anaconda3",
        "source activate base",
        "conda activate cottage_analysis",
        "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/.conda/envs/cottage_analysis/lib/",
        "",
        "",
        "python test.py",
        "",
    ]
    for actual, expected in zip(txt.split("\n"), lines):
        assert actual == expected

    slurm_helper.create_slurm_sbatch(
        tmpdir,
        print_job_id=False,
        conda_env="cottage_analysis",
        python_script="test.py",
        script_name="test.sh",
    )
    with open(tmpdir / "test.sh") as f:
        txt = f.read()
    for actual, expected in zip(txt.split("\n"), lines[:6] + lines[7:]):
        assert actual == expected

    slurm_helper.create_slurm_sbatch(
        tmpdir,
        print_job_id=True,
        conda_env="cottage_analysis",
        python_script="test.py",
        script_name="test.sh",
        env_vars_to_pass={"param": "test", "param2": "test2"},
    )
    with open(tmpdir / "test.sh") as f:
        txt = f.read()

    # running in batch will add the job id to output file
    lines[5] = f"#SBATCH --output={tmpdir}/test_%j.out"
    lines[-2] = "python test.py --param $test --param2 $test2"
    for actual, expected in zip(txt.split("\n"), lines):
        assert actual == expected


def test_python_script_single_func(tmpdir):
    target_file = tmpdir / "test.py"
    slurm_helper.python_script_single_func(
        target_file,
        function_name="test",
        arguments=None,
        vars2parse=None,
        imports=None,
        from_imports=None,
        path2string=True,
    )
    with open(target_file) as f:
        txt = f.read()
    assert txt == "\ntest()\n"

    slurm_helper.python_script_single_func(
        target_file,
        function_name="test",
        arguments={"dir": tmpdir},
        vars2parse=None,
        imports=None,
        from_imports=None,
        path2string=False,
    )
    with open(target_file) as f:
        txt = f.read()
    assert txt == f"\ntest(dir={repr(tmpdir)}, )\n"

    slurm_helper.python_script_single_func(
        target_file,
        function_name="test",
        arguments=None,
        vars2parse=None,
        imports="numpy",
        from_imports=dict(flexiznam="Dataset"),
        path2string=True,
    )
    with open(target_file) as f:
        txt = f.read()
    assert txt == "import numpy\n\nfrom flexiznam import Dataset\n\ntest()\n"

    slurm_helper.python_script_single_func(
        target_file,
        function_name="test",
        arguments=dict(arg1=1, arg2=2),
        vars2parse=None,
        imports=None,
        from_imports=None,
        path2string=True,
    )
    with open(target_file) as f:
        txt = f.read()
    assert txt == "\ntest(arg1=1, arg2=2, )\n"

    slurm_helper.python_script_single_func(
        target_file,
        function_name="test",
        arguments=dict(arg1=1, arg2=2),
        vars2parse=dict(var1="v", var2="vv"),
        imports=None,
        from_imports=None,
        path2string=True,
    )
    with open(target_file) as f:
        txt = f.read()
    lines = [
        "import argparse",
        "",
        "parser = argparse.ArgumentParser()",
        "parser.add_argument('--v')",
        "parser.add_argument('--vv')",
        "args = parser.parse_args()",
        "",
        "test(arg1=1, arg2=2, var1=args.v, var2=args.vv, )",
        "",
    ]
    for expected, actual in zip(lines, txt.split("\n")):
        assert expected == actual


def test_run_slurm_batch():
    script_path = "testpath/testscript.sh"
    cmd = slurm_helper.run_slurm_batch(script_path, dry_run=True)
    assert cmd == f"sbatch {script_path}"
    cmd = slurm_helper.run_slurm_batch(
        script_path, dependency_type="afterok", job_dependency="134", dry_run=True
    )
    assert cmd == f"sbatch --dependency=afterok:134 {script_path}"
    cmd = slurm_helper.run_slurm_batch(
        script_path, dependency_type="dp", job_dependency="134", dry_run=True
    )
    assert cmd == f"sbatch --dependency=dp:134 {script_path}"
    cmd = slurm_helper.run_slurm_batch(
        script_path, env_vars={"var": "value"}, dry_run=True
    )
    assert cmd == f"sbatch --export=var=value {script_path}"
    cmd = slurm_helper.run_slurm_batch(
        script_path, env_vars={"var": "value", "var2": 1}, dry_run=True
    )
    assert cmd == f"sbatch --export=var=value,var2=1 {script_path}"
    cmd = slurm_helper.run_slurm_batch(
        script_path, env_vars={"var": "value"}, job_dependency=12, dry_run=True
    )
    assert cmd == f"sbatch --export=var=value --dependency=afterok:12 {script_path}"


if __name__ == "__main__":
    tmpdir = Path(flz.PARAMETERS["data_root"]["processed"]) / "test"
    test_run_slurm_batch()
    test_python_script_single_func(tmpdir)
    test_create_slurm_sbatch(tmpdir)
    print("ok")
