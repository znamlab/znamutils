from pathlib import Path
from znamutils import slurm_helper

try:
    import flexiznam as flz
except ImportError:
    raise ImportError("flexiznam is required to run this test")


def test_create_slurm_sbatch():
    p = Path(flz.PARAMETERS["data_root"]["processed"]) / "test"
    slurm_helper.create_slurm_sbatch(
        p,
        print_job_id=True,
        conda_env="cottage_analysis",
        python_script="test.py",
        script_name="test.sh",
    )
    with open(p / "test.sh") as f:
        txt = f.read()


if __name__ == "__main__":
    test_create_slurm_sbatch()
