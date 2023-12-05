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


if __name__ == "__main__":
    test_slurm_my_func()
