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
    lines = ["#!/bin/bash",
    "#SBATCH --ntasks=1",
    "#SBATCH --time=12:00:00",
    "#SBATCH --mem=32G",
    "#SBATCH --partition=ncpu",
    "#SBATCH --output=/nemo/lab/znamenskiyp/home/shared/projects/test/test.out",
    "echo \"Job ID: $SLURM_JOB_ID\"",
    "ml Anaconda3",
    "source activate base",
    "conda activate cottage_analysis",
    "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/.conda/envs/cottage_analysis/lib/",
    "",
    "",
    "python test.py",
    ""]
    expected_txt = '\n'.join(lines)
    assert txt == expected_txt

    slurm_helper.create_slurm_sbatch(
        p,
        print_job_id=False,
        conda_env="cottage_analysis",
        python_script="test.py",
        script_name="test.sh",
    )
    with open(p / "test.sh") as f:
        txt = f.read()
    expected_txt = '\n'.join(lines[:6] + lines[7:])
    assert txt == expected_txt

    slurm_helper.create_slurm_sbatch(
        p,
        print_job_id=True,
        conda_env="cottage_analysis",
        python_script="test.py",
        script_name="test.sh",
        env_vars_to_pass={"param": "test", "param2": "test2"},
    )
    with open(p / "test.sh") as f:
        txt = f.read()
    lines[-2] = "python test.py --param $test --param2 $test2"
    assert txt == '\n'.join(lines)

if __name__ == "__main__":
    test_create_slurm_sbatch()
    print('ok')
