from qcelemental.models import Molecule

hydrogen = Molecule.from_data(
    """
    H  0.000000   0.000000   0.000000
    """,
    extras={
        "NOTICE": (
            "This the data parsed in this AtomicResult does NOT "
            "correspond to this molecule. This is a simple Hydrogen atom used "
            "as a placeholder."
        )
    },
)
