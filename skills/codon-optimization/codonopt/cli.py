"""CLI interface for codonopt."""

import sys

import click

from . import core


def _resolve_codon_table(
    organism: str | None,
    table_path: str | None,
    genbank_path: str | None,
    fasta_path: str | None,
    role: str,
) -> tuple[str | None, dict | None]:
    """Resolve organism name or codon table from mutually exclusive CLI options.

    Args:
        organism: Organism name or TaxID.
        table_path: Path to a JSON/CSV codon usage table.
        genbank_path: Path to a GenBank genome file.
        fasta_path: Path to a FASTA genome file.
        role: "target" or "source" (for error messages).

    Returns:
        (organism_name, codon_table) — exactly one will be non-None,
        or both None if nothing was provided.

    Raises:
        click.ClickException: If multiple options are provided.
    """
    provided = []
    if organism is not None:
        provided.append(f"--{role}" if role == "target" else f"--{role}")
    if table_path is not None:
        provided.append(
            "--codon-table" if role == "target" else f"--{role}-codon-table"
        )
    if genbank_path is not None:
        provided.append(f"--{role}-genbank")
    if fasta_path is not None:
        provided.append(f"--{role}-fasta")

    if len(provided) > 1:
        raise click.ClickException(
            f"Only one {role} organism option allowed, but got: {', '.join(provided)}"
        )

    if table_path is not None:
        return None, core.load_codon_table(table_path)
    if genbank_path is not None:
        return None, core.compute_codon_table_from_genbank(genbank_path)
    if fasta_path is not None:
        return None, core.compute_codon_table_from_fasta(fasta_path)
    return organism, None


@click.group()
def cli():
    """Codon optimization and harmonization tool."""


@cli.command()
@click.argument("sequence", required=False)
@click.option("--target", "-t", default=None, help="Target organism (name or TaxID).")
@click.option(
    "--method",
    "-m",
    type=click.Choice(["best_codon", "match_usage"]),
    default="best_codon",
    help="Optimization method.",
)
@click.option(
    "--input-type",
    type=click.Choice(["dna", "protein"]),
    default="dna",
    help="Input sequence type.",
)
@click.option("--output", "-o", type=click.Path(), help="Output FASTA file.")
@click.option(
    "--codon-table",
    type=click.Path(exists=True),
    default=None,
    help="Custom codon usage table (JSON or CSV). Overrides --target.",
)
@click.option(
    "--target-genbank",
    type=click.Path(exists=True),
    default=None,
    help="Compute target codon table from a GenBank genome file.",
)
@click.option(
    "--target-fasta",
    type=click.Path(exists=True),
    default=None,
    help="Compute target codon table from a FASTA genome file (uses Prodigal).",
)
def optimize(sequence, target, method, input_type, output, codon_table, target_genbank, target_fasta):
    """Codon-optimize a DNA or protein sequence."""
    try:
        organism, table = _resolve_codon_table(
            target, codon_table, target_genbank, target_fasta, "target"
        )
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        raise click.ClickException(str(e))

    if organism is None and table is None:
        raise click.ClickException(
            "Provide --target, --codon-table, --target-genbank, or --target-fasta."
        )
    sequence = _read_sequence(sequence)

    try:
        if input_type == "protein":
            result = core.reverse_translate(sequence, organism, method=method, codon_usage_table=table)
        else:
            result = core.optimize(sequence, organism, method=method, codon_usage_table=table)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        raise click.ClickException(str(e))

    _print_optimization_result(result)

    if output:
        _write_fasta(output, f"optimized|{result.target_organism}|{result.method}", result.optimized_seq)
        click.echo(f"\nSequence written to {output}")


@cli.command()
@click.argument("sequence", required=False)
@click.option("--source", "-s", default=None, help="Source organism (native host).")
@click.option("--target", "-t", default=None, help="Target organism (expression host).")
@click.option(
    "--input-type",
    type=click.Choice(["dna", "protein"]),
    default="dna",
    help="Input sequence type.",
)
@click.option("--output", "-o", type=click.Path(), help="Output FASTA file.")
@click.option(
    "--codon-table",
    type=click.Path(exists=True),
    default=None,
    help="Custom target codon usage table (JSON or CSV). Overrides --target.",
)
@click.option(
    "--source-codon-table",
    type=click.Path(exists=True),
    default=None,
    help="Custom source codon usage table (JSON or CSV). Overrides --source.",
)
@click.option(
    "--target-genbank",
    type=click.Path(exists=True),
    default=None,
    help="Compute target codon table from a GenBank genome file.",
)
@click.option(
    "--target-fasta",
    type=click.Path(exists=True),
    default=None,
    help="Compute target codon table from a FASTA genome file (uses Prodigal).",
)
@click.option(
    "--source-genbank",
    type=click.Path(exists=True),
    default=None,
    help="Compute source codon table from a GenBank genome file.",
)
@click.option(
    "--source-fasta",
    type=click.Path(exists=True),
    default=None,
    help="Compute source codon table from a FASTA genome file (uses Prodigal).",
)
def harmonize(
    sequence, source, target, input_type, output,
    codon_table, source_codon_table,
    target_genbank, target_fasta, source_genbank, source_fasta,
):
    """Codon-harmonize a sequence from source to target organism."""
    try:
        target_org, target_table = _resolve_codon_table(
            target, codon_table, target_genbank, target_fasta, "target"
        )
        source_org, source_table = _resolve_codon_table(
            source, source_codon_table, source_genbank, source_fasta, "source"
        )
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        raise click.ClickException(str(e))

    if target_org is None and target_table is None:
        raise click.ClickException(
            "Provide --target, --codon-table, --target-genbank, or --target-fasta."
        )
    if source_org is None and source_table is None:
        raise click.ClickException(
            "Provide --source, --source-codon-table, --source-genbank, or --source-fasta."
        )
    sequence = _read_sequence(sequence)

    try:
        if input_type == "protein":
            # Reverse-translate first, then harmonize the naive DNA
            protein = core.validate_sequence(sequence, "protein")
            if protein.endswith("*"):
                protein = protein[:-1]
            from Bio.Data.CodonTable import standard_dna_table

            back_table = {}
            for codon, aa in standard_dna_table.forward_table.items():
                if aa not in back_table:
                    back_table[aa] = codon
            sequence = "".join(back_table[aa] for aa in protein) + "TAA"

        result = core.harmonize(
            sequence, source_org, target_org,
            codon_usage_table=target_table,
            original_codon_usage_table=source_table,
        )
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        raise click.ClickException(str(e))

    _print_harmonization_result(result)

    if output:
        _write_fasta(
            output,
            f"harmonized|{result.source_organism}->{result.target_organism}",
            result.harmonized_seq,
        )
        click.echo(f"\nSequence written to {output}")


@cli.command("compute-table")
@click.argument("genome_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None, help="Output JSON file path.")
@click.option(
    "--format",
    "file_format",
    type=click.Choice(["auto", "genbank", "fasta"]),
    default="auto",
    help="Input file format. Default: auto-detect by extension.",
)
def compute_table(genome_file, output, file_format):
    """Compute a codon usage table from a genome file (GenBank or FASTA).

    For GenBank files, parses annotated CDS features. For FASTA files, uses
    Prodigal gene prediction to identify coding sequences. The output JSON
    can be used with --codon-table in optimize and harmonize.
    """
    import json

    try:
        table = core.compute_codon_table_from_genome(genome_file, file_format)
    except (ValueError, FileNotFoundError) as e:
        raise click.ClickException(str(e))

    json_str = json.dumps(table, indent=2)

    if output:
        with open(output, "w") as f:
            f.write(json_str)
        click.echo(f"Codon usage table written to {output}")
        click.echo(f"Table covers {len(table)} amino acids")
    else:
        click.echo(json_str)



def _read_sequence(sequence: str | None) -> str:
    """Read sequence from argument or stdin."""
    if sequence:
        return sequence
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise click.ClickException("No sequence provided. Pass as argument or pipe via stdin.")


def _print_optimization_result(result: core.OptimizationResult) -> None:
    click.echo(f"\n{'=' * 50}")
    click.echo(f"Codon Optimization Result")
    click.echo(f"{'=' * 50}")
    click.echo(f"Method:          {result.method}")
    click.echo(f"Target organism: {result.target_organism}")
    click.echo(f"Protein:         {result.protein_seq}")
    click.echo(f"CAI (original):  {result.original_cai:.4f}")
    click.echo(f"CAI (optimized): {result.optimized_cai:.4f}")
    click.echo(f"GC content:      {result.gc_content:.1%}")
    click.echo(f"Codons changed:  {result.codons_changed}/{result.total_codons}")
    click.echo(f"\nOptimized sequence:")
    click.echo(result.optimized_seq)


def _print_harmonization_result(result: core.HarmonizationResult) -> None:
    click.echo(f"\n{'=' * 50}")
    click.echo(f"Codon Harmonization Result")
    click.echo(f"{'=' * 50}")
    click.echo(f"Source organism: {result.source_organism}")
    click.echo(f"Target organism: {result.target_organism}")
    click.echo(f"Protein:         {result.protein_seq}")
    click.echo(f"CAI (original):  {result.original_cai:.4f}")
    click.echo(f"CAI (harmonized):{result.harmonized_cai:.4f}")
    click.echo(f"GC content:      {result.gc_content:.1%}")
    click.echo(f"Codons changed:  {result.codons_changed}/{result.total_codons}")
    click.echo(f"\nHarmonized sequence:")
    click.echo(result.harmonized_seq)


def _write_fasta(path: str, header: str, sequence: str) -> None:
    with open(path, "w") as f:
        f.write(f">{header}\n")
        # Wrap at 80 characters
        for i in range(0, len(sequence), 80):
            f.write(sequence[i : i + 80] + "\n")
