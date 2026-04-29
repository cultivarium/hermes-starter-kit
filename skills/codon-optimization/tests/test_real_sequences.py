"""End-to-end tests using real-world published sequences.

Each test runs sequences through the codonopt tool AND compares
against known published optimized/harmonized sequences from GenBank.

This validates that:
1. The tool produces correct output (protein preserved, CAI improves)
2. The tool's output is comparable to published optimizations
3. The tool works across diverse organisms (bacteria, yeast, human, parasites)
"""

import math
import sys
from io import StringIO

from Bio.Seq import Seq

from codonopt import core
from test_sequences import (
    ALL_SEQUENCES,
    ALGINATE_LYASE_ECOLI,
    CAS9_HUMAN_OPTIMIZED,
    CAS9_NATIVE,
    EGFP_HUMANIZED,
    GFP_MULTI_ORGANISM,
    GFP_WILD_TYPE,
    GFPOPT_GRAM_POSITIVE,
    INSULIN_ECOLI_OPTIMIZED,
    INSULIN_HUMAN_NATIVE,
    MSP142_HARMONIZED,
    MSP142_NATIVE,
    YEGFP3_YEAST,
)


def _strip_stop(protein: str) -> str:
    return protein.rstrip("*")


def _codon_identity(seq_a: str, seq_b: str) -> float:
    """Fraction of codons that are identical between two equal-length sequences."""
    assert len(seq_a) == len(seq_b), f"Length mismatch: {len(seq_a)} vs {len(seq_b)}"
    total = len(seq_a) // 3
    same = sum(
        seq_a[i : i + 3] == seq_b[i : i + 3] for i in range(0, len(seq_a), 3)
    )
    return same / total


def _nucleotide_identity(seq_a: str, seq_b: str) -> float:
    """Fraction of nucleotides that are identical."""
    assert len(seq_a) == len(seq_b)
    return sum(a == b for a, b in zip(seq_a, seq_b)) / len(seq_a)


# ---------------------------------------------------------------------------
# Section 1: GFP optimization across 4 target organisms
# ---------------------------------------------------------------------------


class TestGFPOptimizationMultiOrganism:
    """Optimize wild-type GFP for E. coli, yeast, B. subtilis, and human.

    Compares our tool's output against published codon-optimized GFP
    variants (EGFP, yEGFP3, GFPopt) for the same target organisms.
    """

    def test_gfp_to_ecoli_best_codon(self):
        """GFP -> E. coli: basic optimization."""
        result = core.optimize(GFP_WILD_TYPE["dna_sequence"], "e_coli", method="best_codon")

        assert _strip_stop(result.protein_seq) == GFP_WILD_TYPE["protein_sequence"]
        assert result.optimized_cai == 1.0
        assert result.original_cai < result.optimized_cai
        assert result.codons_changed > 0

    def test_gfp_to_ecoli_match_usage(self):
        """GFP -> E. coli: frequency matching (less aggressive than best_codon)."""
        result = core.optimize(GFP_WILD_TYPE["dna_sequence"], "e_coli", method="match_usage")

        assert _strip_stop(result.protein_seq) == GFP_WILD_TYPE["protein_sequence"]
        # match_usage should improve CAI but not necessarily reach 1.0
        assert result.optimized_cai > result.original_cai
        # match_usage changes fewer codons than best_codon
        best = core.optimize(GFP_WILD_TYPE["dna_sequence"], "e_coli", method="best_codon")
        assert result.codons_changed < best.codons_changed

    def test_gfp_to_yeast_best_codon(self):
        """GFP -> S. cerevisiae: compare against published yEGFP3."""
        result = core.optimize(GFP_WILD_TYPE["dna_sequence"], "s_cerevisiae", method="best_codon")

        assert _strip_stop(result.protein_seq) == GFP_WILD_TYPE["protein_sequence"]
        assert result.optimized_cai == 1.0

        # Published yEGFP3 has S65G and S72A mutations so it's a different protein,
        # but we can still compare codon usage quality
        published_cai = core.compute_cai(YEGFP3_YEAST["dna_sequence"], "s_cerevisiae")
        assert published_cai > 0.85, f"Published yEGFP3 CAI should be high: {published_cai}"
        # Our tool should match or exceed the published version's CAI
        assert result.optimized_cai >= published_cai

    def test_gfp_to_gram_positive_best_codon(self):
        """GFP -> B. subtilis: compare against published GFPopt."""
        result = core.optimize(GFP_WILD_TYPE["dna_sequence"], "b_subtilis", method="best_codon")

        assert _strip_stop(result.protein_seq) == GFP_WILD_TYPE["protein_sequence"]
        assert result.optimized_cai == 1.0

        # Published GFPopt was optimized for B. anthracis (low-GC gram-positive).
        # B. subtilis is also low-GC gram-positive, so CAI should be similar.
        published_cai = core.compute_cai(GFPOPT_GRAM_POSITIVE["dna_sequence"], "b_subtilis")
        assert published_cai > 0.75, f"Published GFPopt CAI(B.sub): {published_cai}"
        # Our tool targets B. subtilis specifically, so should exceed GFPopt
        # which was optimized more broadly for "low-GC gram-positives"
        assert result.optimized_cai >= published_cai

    def test_gfp_to_human_best_codon(self):
        """GFP -> H. sapiens: compare against published EGFP."""
        result = core.optimize(GFP_WILD_TYPE["dna_sequence"], "h_sapiens", method="best_codon")

        assert _strip_stop(result.protein_seq) == GFP_WILD_TYPE["protein_sequence"]
        assert result.optimized_cai == 1.0

        # EGFP has protein mutations so protein differs, but codon usage
        # should be similar quality for human expression
        published_cai = core.compute_cai(EGFP_HUMANIZED["dna_sequence"], "h_sapiens")
        assert published_cai > 0.9, f"Published EGFP CAI(human): {published_cai}"
        assert result.optimized_cai >= published_cai

    def test_gfp_cai_highest_for_target_organism(self):
        """Each GFP variant should have highest CAI for its intended target."""
        organisms = {
            "wild_type_jellyfish": None,  # no specific target
            "human_optimized": "h_sapiens",
            "yeast_optimized": "s_cerevisiae",
            "gram_positive_optimized": "b_subtilis",
        }
        targets = ["e_coli", "h_sapiens", "s_cerevisiae", "b_subtilis"]

        for variant_name, intended_target in organisms.items():
            if intended_target is None:
                continue
            dna = GFP_MULTI_ORGANISM[variant_name]["dna_sequence"]
            target_cai = core.compute_cai(dna, intended_target)
            for other_target in targets:
                if other_target == intended_target:
                    continue
                other_cai = core.compute_cai(dna, other_target)
                assert target_cai >= other_cai, (
                    f"{variant_name}: CAI for intended target {intended_target} "
                    f"({target_cai:.4f}) should be >= CAI for {other_target} "
                    f"({other_cai:.4f})"
                )


# ---------------------------------------------------------------------------
# Section 2: Cas9 optimization (S. pyogenes -> E. coli, human)
# ---------------------------------------------------------------------------


class TestCas9Optimization:
    """SpCas9: large gene (4107 bp) from a gram-positive bacterium.

    Published human-optimized Cas9 provides ground truth for comparison.
    """

    def test_cas9_to_ecoli(self):
        """Cas9 -> E. coli: microbial-to-microbial optimization."""
        result = core.optimize(CAS9_NATIVE["dna_sequence"], "e_coli", method="best_codon")

        assert _strip_stop(result.protein_seq) == _strip_stop(CAS9_NATIVE["protein_sequence"])
        assert result.optimized_cai == 1.0
        assert result.original_cai < 0.7  # native S. pyogenes codons are suboptimal for E. coli

    def test_cas9_to_human_vs_published(self):
        """Cas9 -> human: compare against published human-codon-optimized Cas9."""
        result = core.optimize(CAS9_NATIVE["dna_sequence"], "h_sapiens", method="best_codon")

        # Protein must be identical
        assert _strip_stop(result.protein_seq) == _strip_stop(CAS9_NATIVE["protein_sequence"])
        assert _strip_stop(result.protein_seq) == _strip_stop(CAS9_HUMAN_OPTIMIZED["protein_sequence"])

        # Our CAI should be >= published version
        published_cai = core.compute_cai(CAS9_HUMAN_OPTIMIZED["dna_sequence"], "h_sapiens")
        assert result.optimized_cai >= published_cai

        # Published version should already have high CAI for human
        assert published_cai > 0.9, f"Published humanized Cas9 CAI: {published_cai}"

        # Compare codon choices: our output vs published
        # They won't be identical (different algorithms) but should be similar
        identity = _codon_identity(result.optimized_seq, CAS9_HUMAN_OPTIMIZED["dna_sequence"])
        assert identity > 0.5, (
            f"Codon identity between our output and published: {identity:.1%}. "
            f"Expected >50% agreement since both target human codons."
        )

    def test_cas9_harmonize_gram_positive_to_ecoli(self):
        """Cas9 harmonization: B. subtilis (gram+ proxy) -> E. coli."""
        result = core.harmonize(CAS9_NATIVE["dna_sequence"], "b_subtilis", "e_coli")

        assert _strip_stop(result.protein_seq) == _strip_stop(CAS9_NATIVE["protein_sequence"])
        # Harmonization should improve E. coli CAI vs native
        assert result.harmonized_cai > result.original_cai
        # But harmonization shouldn't reach CAI 1.0 (it preserves usage patterns)
        assert result.harmonized_cai < 1.0


# ---------------------------------------------------------------------------
# Section 3: MSP1-42 harmonization (P. falciparum -> E. coli)
# ---------------------------------------------------------------------------


class TestMSP142Harmonization:
    """MSP1-42: the textbook codon harmonization example.

    Angov et al. (2008) published native and harmonized sequences for the
    P. falciparum MSP1-42 gene expressed in E. coli.

    NOTE: The native MSP1-42 fragment lacks a start codon (partial CDS).
    We test using the full harmonized construct which starts with ATG.
    """

    def test_msp142_harmonized_construct_cai(self):
        """Published harmonized MSP1-42 should have reasonable E. coli CAI."""
        harmonized = MSP142_HARMONIZED["dna_sequence_full_construct"]
        cai = core.compute_cai(harmonized, "e_coli")
        # Harmonization matches frequency profile, doesn't maximize CAI
        assert 0.6 < cai < 1.0, f"Harmonized MSP1-42 CAI: {cai}"

    def test_msp142_native_has_low_ecoli_cai(self):
        """Native P. falciparum MSP1-42 should have low E. coli CAI (AT-biased)."""
        native = MSP142_NATIVE["dna_sequence"]
        cai = core.compute_cai(native, "e_coli")
        # P. falciparum is AT-biased (~80% AT) but CAI measures relative codon
        # frequency, so it's not as low as one might expect. Still should be
        # below the harmonized version.
        assert cai < 0.7, f"Native MSP1-42 E. coli CAI should be moderate: {cai}"

    def test_msp142_harmonized_better_than_native_for_ecoli(self):
        """Harmonized sequence should have higher E. coli CAI than native."""
        native_cai = core.compute_cai(MSP142_NATIVE["dna_sequence"], "e_coli")
        harmonized_cai = core.compute_cai(
            MSP142_HARMONIZED["dna_sequence_msp142_only"], "e_coli"
        )
        assert harmonized_cai > native_cai

    def test_msp142_proteins_identical(self):
        """Native and harmonized MSP1-42 must encode identical proteins."""
        native_prot = MSP142_NATIVE["protein_sequence"]
        harmonized_prot = MSP142_HARMONIZED["protein_sequence_msp142_only"]
        assert native_prot == harmonized_prot

    def test_msp142_optimize_harmonized_construct(self):
        """Re-optimize the already-harmonized construct for E. coli."""
        harmonized = MSP142_HARMONIZED["dna_sequence_full_construct"]
        result = core.optimize(harmonized, "e_coli", method="best_codon")

        # Protein must be preserved
        expected_prot = str(Seq(harmonized).translate()).rstrip("*")
        assert _strip_stop(result.protein_seq) == expected_prot

        # Optimization should improve CAI beyond harmonization
        assert result.optimized_cai >= result.original_cai

    def test_msp142_nucleotide_identity_matches_published(self):
        """Published paper reports ~70.9% nucleotide identity between native/harmonized."""
        native = MSP142_NATIVE["dna_sequence"]
        harmonized = MSP142_HARMONIZED["dna_sequence_msp142_only"]
        identity = _nucleotide_identity(native, harmonized)
        # Paper says 70.9% identity (310/1065 changes = 29.1% changed)
        assert 0.65 < identity < 0.75, (
            f"Nucleotide identity {identity:.1%}, expected ~70.9%"
        )


# ---------------------------------------------------------------------------
# Section 4: Insulin (human -> E. coli)
# ---------------------------------------------------------------------------


class TestInsulinOptimization:
    """Human insulin: classic biotechnology example.

    The native human and E. coli-optimized versions encode different
    protein products (preproinsulin vs M-proinsulin), so we can't
    directly compare sequences. But we can test optimization quality.
    """

    def test_insulin_native_to_ecoli(self):
        """Optimize human preproinsulin for E. coli."""
        result = core.optimize(
            INSULIN_HUMAN_NATIVE["dna_sequence"], "e_coli", method="best_codon"
        )

        assert _strip_stop(result.protein_seq) == _strip_stop(
            INSULIN_HUMAN_NATIVE["protein_sequence"]
        )
        assert result.optimized_cai == 1.0
        assert result.original_cai < result.optimized_cai

    def test_insulin_ecoli_version_already_good(self):
        """Published E. coli-optimized insulin should have high E. coli CAI."""
        cai = core.compute_cai(INSULIN_ECOLI_OPTIMIZED["dna_sequence"], "e_coli")
        assert cai > 0.6, f"Published E. coli insulin CAI: {cai}"

    def test_insulin_reverse_translate_to_ecoli(self):
        """Reverse-translate insulin protein for E. coli."""
        result = core.reverse_translate(
            INSULIN_HUMAN_NATIVE["protein_sequence"], "e_coli"
        )
        assert _strip_stop(result.protein_seq) == _strip_stop(
            INSULIN_HUMAN_NATIVE["protein_sequence"]
        )
        assert result.optimized_cai == 1.0

    def test_insulin_reverse_translate_to_yeast(self):
        """Reverse-translate insulin protein for yeast."""
        result = core.reverse_translate(
            INSULIN_HUMAN_NATIVE["protein_sequence"], "s_cerevisiae"
        )
        assert _strip_stop(result.protein_seq) == _strip_stop(
            INSULIN_HUMAN_NATIVE["protein_sequence"]
        )
        assert result.optimized_cai == 1.0


# ---------------------------------------------------------------------------
# Section 5: Alginate lyase (marine metagenome -> E. coli)
# ---------------------------------------------------------------------------


class TestAlginateLyaseOptimization:
    """Alginate lyase: non-model microbial enzyme optimized for E. coli.

    This sequence was already codon-optimized for E. coli in the published
    version. Re-optimizing should show it's already close to optimal.
    """

    def test_alginate_lyase_already_optimized(self):
        """Published version should already have high E. coli CAI."""
        cai = core.compute_cai(ALGINATE_LYASE_ECOLI["dna_sequence"], "e_coli")
        assert cai > 0.8, f"Published alginate lyase E. coli CAI: {cai}"

    def test_alginate_lyase_reoptimize(self):
        """Re-optimizing should improve to CAI 1.0 but change fewer codons."""
        result = core.optimize(
            ALGINATE_LYASE_ECOLI["dna_sequence"], "e_coli", method="best_codon"
        )
        assert _strip_stop(result.protein_seq) == _strip_stop(
            ALGINATE_LYASE_ECOLI["protein_sequence"]
        )
        assert result.optimized_cai == 1.0
        # Already optimized, so fewer changes needed than a non-optimized gene
        pct_changed = result.codons_changed / result.total_codons
        assert pct_changed < 0.5, (
            f"Already-optimized gene changed {pct_changed:.0%} of codons, "
            f"expected <50%"
        )

    def test_alginate_lyase_to_yeast(self):
        """Optimize the E. coli-optimized version for yeast instead."""
        result = core.optimize(
            ALGINATE_LYASE_ECOLI["dna_sequence"], "s_cerevisiae", method="best_codon"
        )
        assert _strip_stop(result.protein_seq) == _strip_stop(
            ALGINATE_LYASE_ECOLI["protein_sequence"]
        )
        # Yeast CAI should be very different from E. coli CAI
        ecoli_cai = core.compute_cai(result.optimized_seq, "e_coli")
        yeast_cai = core.compute_cai(result.optimized_seq, "s_cerevisiae")
        assert yeast_cai > ecoli_cai, "Yeast-optimized should have higher yeast CAI"


# ---------------------------------------------------------------------------
# Section 6: Cross-organism validation
# ---------------------------------------------------------------------------


class TestCrossOrganismValidation:
    """Validate that optimization is organism-specific.

    Optimizing for one organism should NOT produce high CAI for a
    different organism (unless they happen to share codon preferences).
    """

    def test_ecoli_optimized_bad_for_yeast(self):
        """E. coli-optimized GFP should have lower yeast CAI."""
        result = core.optimize(GFP_WILD_TYPE["dna_sequence"], "e_coli", method="best_codon")
        ecoli_cai = core.compute_cai(result.optimized_seq, "e_coli")
        yeast_cai = core.compute_cai(result.optimized_seq, "s_cerevisiae")
        assert ecoli_cai > yeast_cai

    def test_yeast_optimized_bad_for_ecoli(self):
        """Yeast-optimized GFP should have lower E. coli CAI."""
        result = core.optimize(GFP_WILD_TYPE["dna_sequence"], "s_cerevisiae", method="best_codon")
        ecoli_cai = core.compute_cai(result.optimized_seq, "e_coli")
        yeast_cai = core.compute_cai(result.optimized_seq, "s_cerevisiae")
        assert yeast_cai > ecoli_cai

    def test_human_optimized_bad_for_bsubtilis(self):
        """Human-optimized GFP should have lower B. subtilis CAI."""
        result = core.optimize(GFP_WILD_TYPE["dna_sequence"], "h_sapiens", method="best_codon")
        human_cai = core.compute_cai(result.optimized_seq, "h_sapiens")
        bsub_cai = core.compute_cai(result.optimized_seq, "b_subtilis")
        assert human_cai > bsub_cai


# ---------------------------------------------------------------------------
# Section 7: Sequence comparison report (printed, not asserted)
# ---------------------------------------------------------------------------


def test_print_full_comparison_report(capsys):
    """Print a detailed comparison report for review.

    This test always passes — it generates a human-readable report
    comparing our tool's output against published sequences.
    """
    lines = []
    lines.append("=" * 78)
    lines.append("CODONOPT VALIDATION REPORT: Tool Output vs Published Sequences")
    lines.append("=" * 78)

    # --- GFP across organisms ---
    lines.append("\n## GFP Optimization Across 4 Target Organisms")
    lines.append("-" * 78)

    gfp_dna = GFP_WILD_TYPE["dna_sequence"]
    gfp_targets = [
        ("E. coli", "e_coli", None),
        ("S. cerevisiae", "s_cerevisiae", YEGFP3_YEAST),
        ("B. subtilis", "b_subtilis", GFPOPT_GRAM_POSITIVE),
        ("H. sapiens", "h_sapiens", EGFP_HUMANIZED),
    ]

    for org_name, org_id, published in gfp_targets:
        result = core.optimize(gfp_dna, org_id, method="best_codon")
        lines.append(f"\n  Target: {org_name}")
        lines.append(f"    Our CAI:       {result.original_cai:.4f} -> {result.optimized_cai:.4f}")
        lines.append(f"    Codons changed: {result.codons_changed}/{result.total_codons}")
        lines.append(f"    Protein OK:    {_strip_stop(result.protein_seq) == GFP_WILD_TYPE['protein_sequence']}")

        if published:
            pub_dna = published["dna_sequence"]
            pub_cai = core.compute_cai(pub_dna, org_id)
            lines.append(f"    Published CAI: {pub_cai:.4f} ({published['name']})")
            lines.append(f"    Our CAI >= published: {result.optimized_cai >= pub_cai}")
            if len(result.optimized_seq) == len(pub_dna):
                codon_id = _codon_identity(result.optimized_seq, pub_dna)
                nuc_id = _nucleotide_identity(result.optimized_seq, pub_dna)
                lines.append(f"    Codon identity (ours vs published): {codon_id:.1%}")
                lines.append(f"    Nucleotide identity (ours vs published): {nuc_id:.1%}")

    # --- Cas9 ---
    lines.append("\n\n## SpCas9 Optimization (S. pyogenes -> Human)")
    lines.append("-" * 78)

    cas9_dna = CAS9_NATIVE["dna_sequence"]
    result = core.optimize(cas9_dna, "h_sapiens", method="best_codon")
    pub_dna = CAS9_HUMAN_OPTIMIZED["dna_sequence"]
    pub_cai = core.compute_cai(pub_dna, "h_sapiens")

    lines.append(f"  Our CAI:       {result.original_cai:.4f} -> {result.optimized_cai:.4f}")
    lines.append(f"  Published CAI: {pub_cai:.4f}")
    lines.append(f"  Codons changed: {result.codons_changed}/{result.total_codons}")
    lines.append(f"  Protein OK:    {_strip_stop(result.protein_seq) == _strip_stop(CAS9_NATIVE['protein_sequence'])}")
    codon_id = _codon_identity(result.optimized_seq, pub_dna)
    nuc_id = _nucleotide_identity(result.optimized_seq, pub_dna)
    lines.append(f"  Codon identity (ours vs published): {codon_id:.1%}")
    lines.append(f"  Nucleotide identity (ours vs published): {nuc_id:.1%}")

    # --- Cas9 -> E. coli (microbial target) ---
    lines.append("\n\n## SpCas9 Optimization (S. pyogenes -> E. coli)")
    lines.append("-" * 78)

    result = core.optimize(cas9_dna, "e_coli", method="best_codon")
    lines.append(f"  CAI: {result.original_cai:.4f} -> {result.optimized_cai:.4f}")
    lines.append(f"  Codons changed: {result.codons_changed}/{result.total_codons}")
    lines.append(f"  Protein OK: {_strip_stop(result.protein_seq) == _strip_stop(CAS9_NATIVE['protein_sequence'])}")

    # --- Cas9 harmonization ---
    lines.append("\n\n## SpCas9 Harmonization (B. subtilis proxy -> E. coli)")
    lines.append("-" * 78)

    result = core.harmonize(cas9_dna, "b_subtilis", "e_coli")
    lines.append(f"  CAI: {result.original_cai:.4f} -> {result.harmonized_cai:.4f}")
    lines.append(f"  Codons changed: {result.codons_changed}/{result.total_codons}")
    lines.append(f"  Protein OK: {_strip_stop(result.protein_seq) == _strip_stop(CAS9_NATIVE['protein_sequence'])}")

    # --- MSP1-42 ---
    lines.append("\n\n## MSP1-42 Harmonization (P. falciparum -> E. coli)")
    lines.append("-" * 78)

    native = MSP142_NATIVE["dna_sequence"]
    harmonized = MSP142_HARMONIZED["dna_sequence_msp142_only"]
    native_cai = core.compute_cai(native, "e_coli")
    harmonized_cai = core.compute_cai(harmonized, "e_coli")
    nuc_id = _nucleotide_identity(native, harmonized)

    lines.append(f"  Native CAI (E. coli):     {native_cai:.4f}")
    lines.append(f"  Harmonized CAI (E. coli): {harmonized_cai:.4f}")
    lines.append(f"  Nucleotide identity:       {nuc_id:.1%} (paper reports 70.9%)")
    lines.append(f"  Proteins identical:        {MSP142_NATIVE['protein_sequence'] == MSP142_HARMONIZED['protein_sequence_msp142_only']}")

    # --- Insulin ---
    lines.append("\n\n## Insulin Optimization (Human -> E. coli)")
    lines.append("-" * 78)

    result = core.optimize(INSULIN_HUMAN_NATIVE["dna_sequence"], "e_coli", method="best_codon")
    pub_cai = core.compute_cai(INSULIN_ECOLI_OPTIMIZED["dna_sequence"], "e_coli")

    lines.append(f"  Our CAI:       {result.original_cai:.4f} -> {result.optimized_cai:.4f}")
    lines.append(f"  Published E. coli insulin CAI: {pub_cai:.4f}")
    lines.append(f"  Codons changed: {result.codons_changed}/{result.total_codons}")
    lines.append(f"  Protein OK:    {_strip_stop(result.protein_seq) == _strip_stop(INSULIN_HUMAN_NATIVE['protein_sequence'])}")

    # --- Insulin reverse translation ---
    lines.append("\n\n## Insulin Reverse Translation")
    lines.append("-" * 78)

    for org_name, org_id in [("E. coli", "e_coli"), ("S. cerevisiae", "s_cerevisiae"), ("B. subtilis", "b_subtilis")]:
        result = core.reverse_translate(INSULIN_HUMAN_NATIVE["protein_sequence"], org_id)
        lines.append(f"  -> {org_name}: CAI={result.optimized_cai:.4f}, "
                      f"len={len(result.optimized_seq)} bp, "
                      f"protein OK={_strip_stop(result.protein_seq) == _strip_stop(INSULIN_HUMAN_NATIVE['protein_sequence'])}")

    # --- Alginate lyase ---
    lines.append("\n\n## Alginate Lyase Re-optimization (already E. coli optimized)")
    lines.append("-" * 78)

    alg_dna = ALGINATE_LYASE_ECOLI["dna_sequence"]
    result = core.optimize(alg_dna, "e_coli", method="best_codon")
    lines.append(f"  CAI: {result.original_cai:.4f} -> {result.optimized_cai:.4f}")
    lines.append(f"  Codons changed: {result.codons_changed}/{result.total_codons} "
                  f"({result.codons_changed/result.total_codons:.0%})")
    lines.append(f"  Protein OK: {_strip_stop(result.protein_seq) == _strip_stop(ALGINATE_LYASE_ECOLI['protein_sequence'])}")

    # Optimize for yeast instead
    result_yeast = core.optimize(alg_dna, "s_cerevisiae", method="best_codon")
    lines.append(f"\n  Re-targeted to S. cerevisiae:")
    lines.append(f"    CAI (yeast): {core.compute_cai(alg_dna, 's_cerevisiae'):.4f} -> {result_yeast.optimized_cai:.4f}")
    lines.append(f"    Codons changed: {result_yeast.codons_changed}/{result_yeast.total_codons}")

    lines.append("\n" + "=" * 78)
    lines.append("END OF REPORT")
    lines.append("=" * 78)

    report = "\n".join(lines)
    print(report)

    # Write to file for review
    with open("tests/validation_report.txt", "w") as f:
        f.write(report)
