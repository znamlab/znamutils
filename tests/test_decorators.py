import time
from pathlib import Path

from znamutils import slurm_it

try:
    import flexiznam as flz
except ImportError:
    raise ImportError("flexiznam is required to run this test")


def test_slurm_my_func():
    slurm_folder = (
        Path(flz.PARAMETERS["data_root"]["processed"]) / "test" / "test_slurm_it"
    )
    slurm_folder.mkdir(exist_ok=True)

    @slurm_it(conda_env="cottage_analysis")
    def test_func(a, b):
        return a + b

    assert test_func(1, 2, use_slurm=False) == 3
    assert isinstance(test_func(1, 2, use_slurm=True, slurm_folder=slurm_folder), str)

    @slurm_it(conda_env="cottage_analysis", slurm_options={"time": "00:01:00"})
    def test_func(a, b):
        from datetime import datetime

        print("inner test_func")
        print(a, b)
        print(datetime.now())
        return a + b

    # not using slurm
    out = test_func(1, 2, use_slurm=False)
    assert out == 3
    # using slurm
    out = test_func(1, 2, use_slurm=True, slurm_folder=slurm_folder)
    sbatch_file = slurm_folder / "test_func.sh"
    assert sbatch_file.exists()
    python_file = slurm_folder / "test_func.py"
    assert python_file.exists()

    assert isinstance(out, str)
    # wait for previous job to finish
    test_func(
        1,
        2,
        use_slurm=True,
        scripts_name="test_func_renamed",
        slurm_folder=slurm_folder,
    )
    sbatch_file = slurm_folder / "test_func_renamed.sh"
    assert sbatch_file.exists()

    # rename the slurm script
    test_func(
        1,
        2,
        use_slurm=True,
        scripts_name="test_func_with_dep",
        job_dependency=out,
        slurm_folder=slurm_folder,
    )
    sbatch_file = slurm_folder / "test_func_with_dep.sh"
    assert sbatch_file.exists()

    @slurm_it(
        conda_env="cottage_analysis",
        slurm_options={"time": "00:01:00"},
        imports="numpy",
        from_imports={"pandas": "Dataframe"},
    )
    def test_func(a, b):
        from datetime import datetime

        print("inner test_func")
        print(a, b)
        print(datetime.now())
        return a + b

    test_func(
        1,
        2,
        use_slurm=True,
        scripts_name="test_func_with_dep",
        job_dependency=out,
        slurm_folder=slurm_folder,
    )
    python_file = slurm_folder / "test_func_with_dep.py"
    assert python_file.exists()
    txt = python_file.read_text()
    assert "import numpy" in txt
    assert "from pandas import Dataframe" in txt


def test_dependencies():
    slurm_folder = (
        Path(flz.PARAMETERS["data_root"]["processed"]) / "test" / "test_slurm_it"
    )

    @slurm_it(conda_env="cottage_analysis")
    def slow_func(a, b):
        time.sleep(2)
        return a + b

    o1 = slow_func(1, 2, use_slurm=True, slurm_folder=slurm_folder)
    o2 = slow_func(1, 2, use_slurm=True, slurm_folder=slurm_folder, job_dependency=o1)
    o3 = slow_func(
        1, 2, use_slurm=True, slurm_folder=slurm_folder, job_dependency=[o1, o2]
    )
    o4 = slow_func(
        1,
        2,
        use_slurm=True,
        slurm_folder=slurm_folder,
        job_dependency=",".join([o1, o2, o3]),
    )
    # it work with a list
    slow_func(
        1,
        2,
        use_slurm=True,
        slurm_folder=slurm_folder,
        job_dependency=[o1, o2, o3, o4],
    )
    # it works with empty list
    slow_func(
        1,
        2,
        use_slurm=True,
        slurm_folder=slurm_folder,
        job_dependency=[],
    )


def test_update_slurm_options():
    slurm_folder = (
        Path(flz.PARAMETERS["data_root"]["processed"]) / "test" / "test_slurm_it"
    )
    slurm_folder.mkdir(exist_ok=True)

    @slurm_it(conda_env="cottage_analysis", slurm_options={"time": "00:01:00"})
    def test_func(a, b):
        from datetime import datetime

        print("inner test_func")
        print(a, b)
        print(datetime.now())
        return a + b

    test_func(1, 2, use_slurm=True, slurm_folder=slurm_folder)
    sbatch_file = slurm_folder / "test_func.sh"
    assert sbatch_file.exists()
    with open(sbatch_file, "r") as f:
        txt = f.read()
        assert "#SBATCH --time=00:01:00" in txt
    test_func(
        1,
        2,
        use_slurm=True,
        slurm_folder=slurm_folder,
        slurm_options={"time": "00:02:00"},
    )
    with open(sbatch_file, "r") as f:
        txt = f.read()
        assert "#SBATCH --time=00:02:00" in txt


def test_batch_run(tmpdir):
    @slurm_it(conda_env="cottage_analysis", slurm_options={"time": "00:01:00"})
    def batch_test_func(tardir, a=None, b=None):
        target = str(tardir) + f"/test_{a}.txt"
        with open(target, "w") as f:
            f.write(f"{a} {b}")
        return target

    batch_test_func(
        str(tmpdir),
        use_slurm=True,
        scripts_name="batch_test_func_with_dep",
        slurm_folder=str(tmpdir),
        batch_param_list=[[1, 2], [3, 4]],
        batch_param_names=["a", "b"],
    )
    sh_file = tmpdir / "batch_test_func_with_dep.sh"
    assert sh_file.exists()
    with open(sh_file, "r") as f:
        txt = f.read()
    assert "batch_test_func_with_dep.py --a $a --b $b" in txt
    python_file = tmpdir / "batch_test_func_with_dep.py"
    assert python_file.exists()
    with open(python_file, "r") as f:
        txt = f.read()
    lines = [
        "import argparse",
        "",
        "from test_decorators import batch_test_func",
        "",
        "parser = argparse.ArgumentParser()",
        "parser.add_argument('--a')",
        "parser.add_argument('--b')",
        "args = parser.parse_args()",
        "",
        f"batch_test_func(tardir='{str(tmpdir)}', use_slurm=False, a=args.a, b=args.b, )",
        "",
    ]
    for expected, actual in zip(lines, txt.split("\n")):
        assert expected == actual, f"{expected} != {actual}"


if __name__ == "__main__":
    tmpdir = Path(flz.PARAMETERS["data_root"]["processed"]) / "test"
    test_batch_run(tmpdir)
