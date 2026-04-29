"""Codon optimization and harmonization engine.

Uses DnaChisel for optimization and python-codon-tables for codon
usage data. Provides optimize, harmonize, and reverse_translate functions.
"""

import math
import re
from dataclasses import dataclass, field

from Bio.Data.CodonTable import standard_dna_table
from Bio.Seq import Seq
from dnachisel import CodonOptimize, DnaOptimizationProblem, EnforceTranslation

from .organisms import get_codon_table


# Standard amino acid letters (including stop as *)
_PROTEIN_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY*]+$", re.IGNORECASE)
_DNA_RE = re.compile(r"^[ATGC]+$", re.IGNORECASE)


@dataclass
class OptimizationResult:
    """Result of a codon optimization."""

    original_seq: str
    optimized_seq: str
    protein_seq: str
    method: str
    target_organism: str
    original_cai: float
    optimized_cai: float
    gc_content: float
    codons_changed: int
    total_codons: int


@dataclass
class HarmonizationResult:
    """Result of a codon harmonization."""

    original_seq: str
    harmonized_seq: str
    protein_seq: str
    source_organism: str
    target_organism: str
    original_cai: float
    harmonized_cai: float
    gc_content: float
    codons_changed: int
    total_codons: int


def validate_sequence(seq: str, seq_type: str = "dna") -> str:
    """Validate and clean a DNA or protein sequence.

    Args:
        seq: Input sequence string.
        seq_type: "dna" or "protein".

    Returns:
        Cleaned uppercase sequence with whitespace removed.

    Raises:
        ValueError: If the sequence is invalid.
    """
    cleaned = re.sub(r"\s+", "", seq).upper()
    if not cleaned:
        raise ValueError("Empty sequence")

    if seq_type == "dna":
        if not _DNA_RE.match(cleaned):
            raise ValueError(
                f"Invalid DNA sequence: contains non-ATGC characters"
            )
        if len(cleaned) % 3 != 0:
            raise ValueError(
                f"DNA sequence length ({len(cleaned)}) is not a multiple of 3"
            )
        if not cleaned.startswith("ATG"):
            raise ValueError("DNA sequence does not start with ATG start codon")
    elif seq_type == "protein":
        if not _PROTEIN_RE.match(cleaned):
            raise ValueError("Invalid protein sequence: contains non-standard amino acids")
        if not cleaned.startswith("M"):
            raise ValueError("Protein sequence does not start with M (methionine)")
    else:
        raise ValueError(f"Unknown sequence type: {seq_type!r} (use 'dna' or 'protein')")

    return cleaned


def load_codon_table(path: str) -> dict[str, dict[str, float]]:
    """Load a codon usage table from a JSON or CSV file.

    JSON format: {"A": {"GCT": 0.38, "GCC": 0.27, ...}, ...}
    CSV format: amino_acid,codon,frequency (one row per codon, header line)

    Args:
        path: Path to JSON or CSV file.

    Returns:
        Codon usage table dict.
    """
    import csv
    import json

    with open(path) as f:
        content = f.read().strip()

    # Try JSON first
    if content.startswith("{"):
        return json.loads(content)

    # Fall back to CSV
    table: dict[str, dict[str, float]] = {}
    reader = csv.reader(content.splitlines())
    next(reader)  # skip header
    for row in reader:
        aa, codon, freq = row[0].strip(), row[1].strip().upper(), float(row[2])
        if aa not in table:
            table[aa] = {}
        table[aa][codon] = freq
    return table


def compute_cai(
    sequence: str,
    species: str | None = None,
    codon_usage_table: dict[str, dict[str, float]] | None = None,
) -> float:
    """Compute the Codon Adaptation Index for a DNA sequence.

    CAI measures how well codon usage matches the preferred codons
    of the target organism. 1.0 = all optimal codons, lower = less optimal.

    Args:
        sequence: DNA sequence (length must be multiple of 3).
        species: Organism name or TaxID for codon table lookup.
        codon_usage_table: Custom codon usage table. If provided,
            species is ignored.

    Returns:
        CAI value between 0.0 and 1.0.
    """
    if codon_usage_table is not None:
        table = codon_usage_table
    elif species is not None:
        table = get_codon_table(species)
    else:
        raise ValueError("Provide either species or codon_usage_table")
    codons = [sequence[i : i + 3] for i in range(0, len(sequence), 3)]
    log_sum = 0.0
    n = 0
    for codon in codons:
        # Find which amino acid this codon encodes
        aa = None
        for amino_acid, codon_freqs in table.items():
            if codon in codon_freqs:
                aa = amino_acid
                break
        if aa is None or aa == "*":
            continue
        freq = table[aa][codon]
        max_freq = max(table[aa].values())
        if freq == 0 or max_freq == 0:
            return 0.0
        log_sum += math.log(freq / max_freq)
        n += 1
    if n == 0:
        return 0.0
    return math.exp(log_sum / n)


def _gc_content(seq: str) -> float:
    """Compute GC content as a fraction."""
    gc = sum(1 for c in seq if c in "GC")
    return gc / len(seq) if seq else 0.0


def _count_codon_changes(original: str, optimized: str) -> tuple[int, int]:
    """Count changed codons between two sequences of equal length."""
    total = len(original) // 3
    changed = sum(
        original[i : i + 3] != optimized[i : i + 3]
        for i in range(0, len(original), 3)
    )
    return changed, total


def _translate(dna_seq: str) -> str:
    """Translate a DNA sequence to protein."""
    return str(Seq(dna_seq).translate())


def optimize(
    dna_seq: str,
    target_organism: str | None = None,
    method: str = "best_codon",
    codon_usage_table: dict[str, dict[str, float]] | None = None,
) -> OptimizationResult:
    """Codon-optimize a DNA sequence for a target organism.

    Args:
        dna_seq: DNA coding sequence (must be multiple of 3, start with ATG).
        target_organism: Organism name or TaxID (e.g. "e_coli", 316407).
            Optional if codon_usage_table is provided.
        method: "best_codon" (maximize CAI) or "match_usage" (match frequency profile).
        codon_usage_table: Custom codon usage table (e.g. from load_codon_table).
            If provided, this table is used instead of looking up by organism name.

    Returns:
        OptimizationResult with original and optimized sequences plus metrics.

    Raises:
        ValueError: If method is unknown or sequence is invalid.
    """
    dna_seq = validate_sequence(dna_seq, "dna")

    if codon_usage_table is None and target_organism is None:
        raise ValueError("Provide either target_organism or codon_usage_table")

    method_map = {
        "best_codon": "use_best_codon",
        "match_usage": "match_codon_usage",
    }
    if method not in method_map:
        raise ValueError(f"Unknown method {method!r}. Use 'best_codon' or 'match_usage'.")
    dnachisel_method = method_map[method]

    objective_kwargs: dict = {"method": dnachisel_method}
    if codon_usage_table is not None:
        objective_kwargs["codon_usage_table"] = codon_usage_table
    else:
        objective_kwargs["species"] = target_organism

    problem = DnaOptimizationProblem(
        sequence=dna_seq,
        objectives=[CodonOptimize(**objective_kwargs)],
        constraints=[EnforceTranslation()],
        logger=None,
    )
    problem.resolve_constraints()
    problem.optimize()

    optimized = problem.sequence
    changed, total = _count_codon_changes(dna_seq, optimized)

    label = str(target_organism) if target_organism else "custom_table"

    return OptimizationResult(
        original_seq=dna_seq,
        optimized_seq=optimized,
        protein_seq=_translate(optimized),
        method=method,
        target_organism=label,
        original_cai=compute_cai(dna_seq, species=target_organism, codon_usage_table=codon_usage_table),
        optimized_cai=compute_cai(optimized, species=target_organism, codon_usage_table=codon_usage_table),
        gc_content=_gc_content(optimized),
        codons_changed=changed,
        total_codons=total,
    )


def harmonize(
    dna_seq: str,
    source_organism: str | None = None,
    target_organism: str | None = None,
    codon_usage_table: dict[str, dict[str, float]] | None = None,
    original_codon_usage_table: dict[str, dict[str, float]] | None = None,
) -> HarmonizationResult:
    """Codon-harmonize a DNA sequence from source to target organism.

    Harmonization preserves the codon usage pattern of the source organism
    by mapping Relative Codon Adaptiveness (RCA) values to the target
    organism's codon table, rather than simply maximizing CAI.

    Args:
        dna_seq: DNA coding sequence.
        source_organism: Native host organism name or TaxID.
            Optional if original_codon_usage_table is provided.
        target_organism: Expression host organism name or TaxID.
            Optional if codon_usage_table is provided.
        codon_usage_table: Custom target codon usage table.
        original_codon_usage_table: Custom source codon usage table.

    Returns:
        HarmonizationResult with original and harmonized sequences plus metrics.
    """
    dna_seq = validate_sequence(dna_seq, "dna")

    if codon_usage_table is None and target_organism is None:
        raise ValueError("Provide either target_organism or codon_usage_table")
    if original_codon_usage_table is None and source_organism is None:
        raise ValueError("Provide either source_organism or original_codon_usage_table")

    objective_kwargs: dict = {"method": "harmonize_rca"}
    if codon_usage_table is not None:
        objective_kwargs["codon_usage_table"] = codon_usage_table
    else:
        objective_kwargs["species"] = target_organism
    if original_codon_usage_table is not None:
        objective_kwargs["original_codon_usage_table"] = original_codon_usage_table
    else:
        objective_kwargs["original_species"] = source_organism

    problem = DnaOptimizationProblem(
        sequence=dna_seq,
        objectives=[CodonOptimize(**objective_kwargs)],
        constraints=[EnforceTranslation()],
        logger=None,
    )
    problem.resolve_constraints()
    problem.optimize()

    harmonized = problem.sequence
    changed, total = _count_codon_changes(dna_seq, harmonized)

    source_label = str(source_organism) if source_organism else "custom_table"
    target_label = str(target_organism) if target_organism else "custom_table"

    return HarmonizationResult(
        original_seq=dna_seq,
        harmonized_seq=harmonized,
        protein_seq=_translate(harmonized),
        source_organism=source_label,
        target_organism=target_label,
        original_cai=compute_cai(dna_seq, species=target_organism, codon_usage_table=codon_usage_table),
        harmonized_cai=compute_cai(harmonized, species=target_organism, codon_usage_table=codon_usage_table),
        gc_content=_gc_content(harmonized),
        codons_changed=changed,
        total_codons=total,
    )


def reverse_translate(
    protein_seq: str,
    target_organism: str | None = None,
    method: str = "best_codon",
    codon_usage_table: dict[str, dict[str, float]] | None = None,
) -> OptimizationResult:
    """Reverse-translate a protein sequence to optimized DNA.

    Creates a naive DNA sequence using the standard codon table,
    then optimizes it for the target organism.

    Args:
        protein_seq: Amino acid sequence (single-letter codes).
        target_organism: Organism name or TaxID. Optional if
            codon_usage_table is provided.
        method: "best_codon" or "match_usage".
        codon_usage_table: Custom codon usage table.

    Returns:
        OptimizationResult (original_seq is the naive back-translation).
    """
    protein_seq = validate_sequence(protein_seq, "protein")

    # Strip trailing stop if present
    if protein_seq.endswith("*"):
        protein_seq = protein_seq[:-1]

    # Naive reverse translation: use first codon from standard table
    back_table = {}
    for codon, aa in standard_dna_table.forward_table.items():
        if aa not in back_table:
            back_table[aa] = codon

    naive_dna = "".join(back_table[aa] for aa in protein_seq)
    # Add stop codon
    naive_dna += "TAA"

    return optimize(naive_dna, target_organism, method=method, codon_usage_table=codon_usage_table)


def _cds_sequences_to_codon_table(
    cds_sequences: list[str],
) -> dict[str, dict[str, float]]:
    """Count codons from CDS sequences and return a frequency table.

    Args:
        cds_sequences: List of uppercase DNA coding sequences. Each must
            be a multiple of 3 and at least 6 bp.

    Returns:
        Codon usage table dict: {"A": {"GCT": 0.38, "GCC": 0.27, ...}, ...}

    Raises:
        ValueError: If no valid CDS sequences are provided.
    """
    counts: dict[str, dict[str, int]] = {}
    for codon, aa in standard_dna_table.forward_table.items():
        if aa not in counts:
            counts[aa] = {}
        counts[aa][codon] = 0

    cds_count = 0
    for cds_seq in cds_sequences:
        if len(cds_seq) % 3 != 0 or len(cds_seq) < 6:
            continue
        cds_count += 1
        # Count codons, skip the final stop codon
        for i in range(0, len(cds_seq) - 3, 3):
            codon = cds_seq[i : i + 3]
            if not _DNA_RE.match(codon):
                continue
            if codon in standard_dna_table.forward_table:
                aa = standard_dna_table.forward_table[codon]
                if aa in counts and codon in counts[aa]:
                    counts[aa][codon] += 1

    if cds_count == 0:
        raise ValueError("No valid CDS sequences provided")

    table: dict[str, dict[str, float]] = {}
    for aa, codon_counts in counts.items():
        total = sum(codon_counts.values())
        if total == 0:
            continue
        table[aa] = {codon: count / total for codon, count in codon_counts.items()}

    return table


def compute_codon_table_from_genbank(genbank_path: str) -> dict[str, dict[str, float]]:
    """Compute a codon usage table from a genome GenBank file.

    Parses all CDS features from the GenBank file, extracts coding sequences,
    and computes per-amino-acid codon usage frequencies. Useful for non-model
    organisms not available in the Kazusa database.

    Args:
        genbank_path: Path to a GenBank (.gb, .gbk, or .gbff) file.

    Returns:
        Codon usage table dict: {"A": {"GCT": 0.38, "GCC": 0.27, ...}, ...}

    Raises:
        ValueError: If no CDS features are found in the file.
    """
    from Bio import SeqIO

    cds_sequences = []
    for record in SeqIO.parse(genbank_path, "genbank"):
        for feature in record.features:
            if feature.type != "CDS":
                continue
            if "pseudo" in feature.qualifiers or "pseudogene" in feature.qualifiers:
                continue
            try:
                cds_seq = str(feature.extract(record.seq)).upper()
            except Exception:
                continue
            cds_sequences.append(cds_seq)

    if not cds_sequences:
        raise ValueError(f"No CDS features found in {genbank_path}")

    return _cds_sequences_to_codon_table(cds_sequences)


def compute_codon_table_from_fasta(fasta_path: str) -> dict[str, dict[str, float]]:
    """Compute a codon usage table from a FASTA genome file.

    Uses pyrodigal to predict genes from the nucleotide sequences,
    then counts codons from predicted CDS regions.

    Args:
        fasta_path: Path to a FASTA (.fa, .fasta, or .fna) file.

    Returns:
        Codon usage table dict: {"A": {"GCT": 0.38, "GCC": 0.27, ...}, ...}

    Raises:
        ValueError: If no genes are predicted from the input.
    """
    import pyrodigal
    from Bio import SeqIO

    gene_finder = pyrodigal.GeneFinder(meta=True)

    cds_sequences = []
    for record in SeqIO.parse(fasta_path, "fasta"):
        seq_str = str(record.seq).upper()
        if len(seq_str) < 20:
            continue
        genes = gene_finder.find_genes(seq_str.encode())
        for gene in genes:
            # Extract nucleotide sequence for this gene
            # pyrodigal gene coordinates are 1-based
            start = gene.begin - 1
            end = gene.end
            if gene.strand == -1:
                cds_seq = str(Seq(seq_str[start:end]).reverse_complement())
            else:
                cds_seq = seq_str[start:end]
            cds_sequences.append(cds_seq)

    if not cds_sequences:
        raise ValueError(f"No genes predicted from {fasta_path}")

    return _cds_sequences_to_codon_table(cds_sequences)


_GENBANK_EXTENSIONS = {".gb", ".gbk", ".gbff"}
_FASTA_EXTENSIONS = {".fa", ".fasta", ".fna"}


def compute_codon_table_from_genome(
    path: str, file_format: str = "auto"
) -> dict[str, dict[str, float]]:
    """Compute a codon usage table from a genome file.

    Auto-detects format by file extension, or uses the specified format.

    Args:
        path: Path to a genome file (GenBank or FASTA).
        file_format: "auto" (detect by extension), "genbank", or "fasta".

    Returns:
        Codon usage table dict.

    Raises:
        ValueError: If format cannot be determined or no genes are found.
    """
    import os

    if file_format == "auto":
        ext = os.path.splitext(path)[1].lower()
        if ext in _GENBANK_EXTENSIONS:
            file_format = "genbank"
        elif ext in _FASTA_EXTENSIONS:
            file_format = "fasta"
        else:
            raise ValueError(
                f"Cannot auto-detect format for extension '{ext}'. "
                f"Use --format genbank or --format fasta."
            )

    if file_format == "genbank":
        return compute_codon_table_from_genbank(path)
    elif file_format == "fasta":
        return compute_codon_table_from_fasta(path)
    else:
        raise ValueError(f"Unknown format: {file_format!r}")


def compare_sequences(original: str, optimized: str) -> str:
    """Generate a side-by-side codon comparison of two sequences.

    Args:
        original: Original DNA sequence.
        optimized: Optimized DNA sequence (same length).

    Returns:
        Formatted string showing codon-by-codon changes.
    """
    if len(original) != len(optimized):
        raise ValueError("Sequences must be the same length")

    lines = [f"{'Pos':<6} {'Original':<10} {'Optimized':<10} {'Changed'}"]
    lines.append("-" * 40)

    for i in range(0, len(original), 3):
        orig_codon = original[i : i + 3]
        opt_codon = optimized[i : i + 3]
        pos = i // 3 + 1
        changed = "*" if orig_codon != opt_codon else ""
        lines.append(f"{pos:<6} {orig_codon:<10} {opt_codon:<10} {changed}")

    changed, total = _count_codon_changes(original, optimized)
    lines.append("")
    lines.append(f"Total: {changed}/{total} codons changed ({100*changed/total:.1f}%)")
    return "\n".join(lines)
