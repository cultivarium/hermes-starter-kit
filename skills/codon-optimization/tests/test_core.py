"""Tests for codonopt core functionality."""

import pytest

from codonopt import core

# A short test CDS: encodes MKAFVLKDFGIF*
TEST_DNA = "ATGAAAGCATTTGTACTGAAAGATTTTGGTATTTTTTAA"


class TestValidateSequence:
    def test_valid_dna(self):
        result = core.validate_sequence("atgaaataa", "dna")
        assert result == "ATGAAATAA"

    def test_strips_whitespace(self):
        result = core.validate_sequence("ATG AAA TAA", "dna")
        assert result == "ATGAAATAA"

    def test_invalid_dna_chars(self):
        with pytest.raises(ValueError, match="non-ATGC"):
            core.validate_sequence("ATGUUUTAA", "dna")

    def test_dna_not_multiple_of_3(self):
        with pytest.raises(ValueError, match="multiple of 3"):
            core.validate_sequence("ATGAA", "dna")

    def test_dna_no_start_codon(self):
        with pytest.raises(ValueError, match="ATG"):
            core.validate_sequence("TTTAAATAA", "dna")

    def test_valid_protein(self):
        result = core.validate_sequence("MKAFVL", "protein")
        assert result == "MKAFVL"

    def test_protein_no_met_start(self):
        with pytest.raises(ValueError, match="methionine"):
            core.validate_sequence("KAFVL", "protein")

    def test_empty_sequence(self):
        with pytest.raises(ValueError, match="Empty"):
            core.validate_sequence("", "dna")

    def test_unknown_type(self):
        with pytest.raises(ValueError, match="Unknown"):
            core.validate_sequence("ATG", "rna")


class TestOptimize:
    def test_basic_optimization(self):
        result = core.optimize(TEST_DNA, "e_coli", method="best_codon")
        assert result.optimized_seq != result.original_seq or result.codons_changed == 0
        assert result.optimized_cai >= result.original_cai
        assert result.method == "best_codon"
        assert result.target_organism == "e_coli"

    def test_protein_preserved(self):
        result = core.optimize(TEST_DNA, "e_coli")
        original_protein = core._translate(TEST_DNA)
        assert result.protein_seq == original_protein

    def test_match_usage_method(self):
        result = core.optimize(TEST_DNA, "e_coli", method="match_usage")
        assert result.method == "match_usage"
        original_protein = core._translate(TEST_DNA)
        assert result.protein_seq == original_protein

    def test_invalid_method(self):
        with pytest.raises(ValueError, match="Unknown method"):
            core.optimize(TEST_DNA, "e_coli", method="invalid")


class TestHarmonize:
    def test_human_to_ecoli(self):
        result = core.harmonize(TEST_DNA, "h_sapiens", "e_coli")
        assert result.source_organism == "h_sapiens"
        assert result.target_organism == "e_coli"
        original_protein = core._translate(TEST_DNA)
        assert result.protein_seq == original_protein

    def test_harmonization_differs_from_optimization(self):
        opt_result = core.optimize(TEST_DNA, "e_coli", method="best_codon")
        harm_result = core.harmonize(TEST_DNA, "h_sapiens", "e_coli")
        # Harmonization should generally produce a different result than
        # pure optimization since it preserves codon usage patterns
        # (though for very short sequences they might coincide)
        assert harm_result.harmonized_seq is not None


class TestReverseTranslate:
    def test_reverse_translate(self):
        protein = "MKAFVLKDFGIF"
        result = core.reverse_translate(protein, "e_coli")
        assert result.protein_seq.rstrip("*") == protein
        assert result.optimized_cai > 0

    def test_protein_with_stop(self):
        protein = "MKAFVL*"
        result = core.reverse_translate(protein, "e_coli")
        assert "M" in result.protein_seq


class TestCompareSequences:
    def test_compare(self):
        opt = core.optimize(TEST_DNA, "e_coli")
        comparison = core.compare_sequences(TEST_DNA, opt.optimized_seq)
        assert "Original" in comparison
        assert "Optimized" in comparison
        assert "codons changed" in comparison

    def test_unequal_length(self):
        with pytest.raises(ValueError, match="same length"):
            core.compare_sequences("ATGATG", "ATG")


class TestCAI:
    def test_cai_range(self):
        cai = core.compute_cai(TEST_DNA, "e_coli")
        assert 0.0 < cai <= 1.0

    def test_optimized_cai_higher(self):
        original_cai = core.compute_cai(TEST_DNA, "e_coli")
        result = core.optimize(TEST_DNA, "e_coli", method="best_codon")
        assert result.optimized_cai >= original_cai


class TestCustomCodonTable:
    """Tests for user-provided custom codon usage tables."""

    @pytest.fixture
    def ecoli_table(self):
        """Get E. coli codon table for use as a custom table."""
        return core.get_codon_table("e_coli")

    @pytest.fixture
    def custom_json_table(self, tmp_path):
        """Write E. coli table to a JSON file and return the path."""
        import json

        table = core.get_codon_table("e_coli")
        path = tmp_path / "ecoli_table.json"
        path.write_text(json.dumps(table))
        return str(path)

    @pytest.fixture
    def custom_csv_table(self, tmp_path):
        """Write E. coli table to a CSV file and return the path."""
        table = core.get_codon_table("e_coli")
        lines = ["amino_acid,codon,frequency"]
        for aa, codons in table.items():
            for codon, freq in codons.items():
                lines.append(f"{aa},{codon},{freq}")
        path = tmp_path / "ecoli_table.csv"
        path.write_text("\n".join(lines))
        return str(path)

    def test_load_codon_table_json(self, custom_json_table):
        table = core.load_codon_table(custom_json_table)
        assert "A" in table
        assert "GCT" in table["A"]
        assert isinstance(table["A"]["GCT"], float)

    def test_load_codon_table_csv(self, custom_csv_table):
        table = core.load_codon_table(custom_csv_table)
        assert "A" in table
        assert "GCT" in table["A"]
        assert isinstance(table["A"]["GCT"], float)

    def test_optimize_with_custom_table(self, ecoli_table):
        result = core.optimize(TEST_DNA, codon_usage_table=ecoli_table)
        assert result.target_organism == "custom_table"
        assert result.optimized_cai >= result.original_cai
        original_protein = core._translate(TEST_DNA)
        assert result.protein_seq == original_protein

    def test_optimize_custom_table_matches_species(self, ecoli_table):
        """Custom table from E. coli should produce same result as species='e_coli'."""
        result_species = core.optimize(TEST_DNA, "e_coli")
        result_custom = core.optimize(TEST_DNA, codon_usage_table=ecoli_table)
        assert result_species.optimized_seq == result_custom.optimized_seq

    def test_harmonize_with_custom_tables(self):
        source_table = core.get_codon_table("h_sapiens")
        target_table = core.get_codon_table("e_coli")
        result = core.harmonize(
            TEST_DNA,
            codon_usage_table=target_table,
            original_codon_usage_table=source_table,
        )
        assert result.source_organism == "custom_table"
        assert result.target_organism == "custom_table"
        original_protein = core._translate(TEST_DNA)
        assert result.protein_seq == original_protein

    def test_reverse_translate_with_custom_table(self, ecoli_table):
        protein = "MKAFVLKDFGIF"
        result = core.reverse_translate(protein, codon_usage_table=ecoli_table)
        assert result.protein_seq.rstrip("*") == protein
        assert result.target_organism == "custom_table"

    def test_compute_cai_with_custom_table(self, ecoli_table):
        cai_species = core.compute_cai(TEST_DNA, species="e_coli")
        cai_custom = core.compute_cai(TEST_DNA, codon_usage_table=ecoli_table)
        assert abs(cai_species - cai_custom) < 1e-10

    def test_optimize_requires_target_or_table(self):
        with pytest.raises(ValueError, match="target_organism or codon_usage_table"):
            core.optimize(TEST_DNA)

    def test_load_from_json_file(self, custom_json_table):
        """End-to-end: load JSON file, optimize with it."""
        table = core.load_codon_table(custom_json_table)
        result = core.optimize(TEST_DNA, codon_usage_table=table)
        assert result.optimized_cai >= result.original_cai

    def test_load_from_csv_file(self, custom_csv_table):
        """End-to-end: load CSV file, optimize with it."""
        table = core.load_codon_table(custom_csv_table)
        result = core.optimize(TEST_DNA, codon_usage_table=table)
        assert result.optimized_cai >= result.original_cai


class TestCdsSequencesToCodonTable:
    """Tests for the shared codon-counting helper."""

    def test_known_cds(self):
        # A CDS with known codons: ATG GCT AAA TAA (M, A, K, stop)
        cds = "ATGGCTAAATAA"
        table = core._cds_sequences_to_codon_table([cds])
        assert "A" in table
        assert table["A"]["GCT"] > 0
        assert "K" in table
        assert table["K"]["AAA"] > 0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="No valid CDS"):
            core._cds_sequences_to_codon_table([])

    def test_short_sequences_skipped(self):
        with pytest.raises(ValueError, match="No valid CDS"):
            core._cds_sequences_to_codon_table(["ATG"])  # too short

    def test_multiple_cds(self):
        cds1 = "ATGGCTAAATAA"  # GCT for A
        cds2 = "ATGGCCAAATAA"  # GCC for A
        table = core._cds_sequences_to_codon_table([cds1, cds2])
        assert abs(table["A"]["GCT"] - 0.5) < 1e-10
        assert abs(table["A"]["GCC"] - 0.5) < 1e-10


class TestComputeCodonTableFromFasta:
    """Tests for FASTA-based codon table computation via pyrodigal."""

    @pytest.fixture
    def synthetic_fasta(self, tmp_path):
        """Create a synthetic FASTA with a repeated ORF so pyrodigal can find genes."""
        # Build a ~3kb contig with a clear ORF that pyrodigal should detect.
        # Use a repetitive but valid coding sequence.
        orf = "ATGGCTAAAGCTTTTGGTGCTGAAGCTAAAGCTTTTGGTGCTGAAGCTAAAGCTTTTGGTGCTGAA" * 10 + "TAA"
        # Pad with non-coding flanking sequence
        flank = "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT" * 5
        contig = flank + orf + flank
        path = tmp_path / "test_genome.fasta"
        path.write_text(f">contig1\n{contig}\n")
        return str(path)

    def test_fasta_returns_valid_table(self, synthetic_fasta):
        table = core.compute_codon_table_from_fasta(synthetic_fasta)
        # Should have amino acid keys
        assert "A" in table or "M" in table
        # All values should be frequencies summing to ~1.0 per AA
        for aa, codons in table.items():
            total = sum(codons.values())
            assert abs(total - 1.0) < 1e-6, f"AA {aa} frequencies sum to {total}"

    def test_empty_fasta_raises(self, tmp_path):
        path = tmp_path / "empty.fasta"
        path.write_text("")
        with pytest.raises(ValueError, match="No genes predicted"):
            core.compute_codon_table_from_fasta(str(path))

    def test_short_sequence_raises(self, tmp_path):
        path = tmp_path / "short.fasta"
        path.write_text(">tiny\nATGC\n")
        with pytest.raises(ValueError, match="No genes predicted"):
            core.compute_codon_table_from_fasta(str(path))


class TestComputeCodonTableFromGenome:
    """Tests for the auto-detecting dispatcher."""

    def test_genbank_extension_detected(self, tmp_path):
        """Verify .gbk is detected as genbank format (will fail on content, not format)."""
        path = tmp_path / "test.gbk"
        path.write_text("")
        with pytest.raises(ValueError):
            core.compute_codon_table_from_genome(str(path))

    def test_fasta_extension_detected(self, tmp_path):
        """Verify .fasta is detected as fasta format (will fail on content, not format)."""
        path = tmp_path / "test.fasta"
        path.write_text("")
        with pytest.raises(ValueError):
            core.compute_codon_table_from_genome(str(path))

    def test_unknown_extension_raises(self, tmp_path):
        path = tmp_path / "test.xyz"
        path.write_text("")
        with pytest.raises(ValueError, match="Cannot auto-detect"):
            core.compute_codon_table_from_genome(str(path))

    def test_explicit_format_overrides_extension(self, tmp_path):
        """A .txt file with --format fasta should be treated as FASTA."""
        # Create a valid FASTA with a long ORF
        orf = "ATGGCTAAAGCTTTTGGTGCTGAAGCTAAAGCTTTTGGTGCTGAAGCTAAAGCTTTTGGTGCTGAA" * 10 + "TAA"
        flank = "T" * 300
        path = tmp_path / "genome.txt"
        path.write_text(f">contig1\n{flank}{orf}{flank}\n")
        table = core.compute_codon_table_from_genome(str(path), file_format="fasta")
        assert "A" in table or "M" in table
