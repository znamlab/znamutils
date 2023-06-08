from pathlib import Path
from znamutils import slurm_helper

try:
    import flexiznam as flz
except ImportError:
    raise ImportError("flexiznam is required to run this test")


def test_create_slurm_sbatch():
    p = Path(flz.PARAMETERS["data_root"]["processed"]) / "test"
