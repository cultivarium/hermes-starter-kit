"""Organism lookup for codon usage tables.

Wraps python-codon-tables to provide codon table retrieval by NCBI TaxID.
"""

import python_codon_tables as pct


def get_codon_table(identifier: str | int) -> dict[str, dict[str, float]]:
    """Get a codon usage table by NCBI TaxID from the Kazusa database.

    Args:
        identifier: NCBI TaxID (e.g. 316407) or string TaxID
            (e.g. "316407"). Fetched from the Kazusa codon usage
            database.

    Returns:
        Dict mapping amino acid single-letter codes (plus "*" for stop)
        to dicts of codon -> relative frequency.

    Raises:
        RuntimeError: If the TaxID is not found on Kazusa or the server is down.
    """
    return pct.get_codons_table(identifier)
