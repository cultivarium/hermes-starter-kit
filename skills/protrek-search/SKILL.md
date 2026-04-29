---
name: protrek-search
description: Use when the user needs trimodal protein search over UniProt/Swiss-Prot — natural-language function-to-protein retrieval, sequence-to-function annotation, or cross-modal (sequence/structure/text) search via ProTrek. Covers semantic protein-function queries ("find proteins that bind heme and act as peroxidases"), sequence-to-text annotation, and text-to-sequence retrieval. Do NOT use for GenBank/NCBI nt/nr BLAST searches, profile-HMM homology (PHMMER/HMMER), structure-database searches (FoldSeek/PDB/AlphaFold), or MMseqs2 clustering — those use dedicated tools.
---

# ProTrek Search

ProTrek is a trimodal protein language model that indexes Swiss-Prot, UniRef50, OMG_prot50, NCBI, GOPC, and related databases. It supports pairwise retrieval across three modalities: **sequence** (amino-acid string), **structure** (Foldseek 3Di string), and **text** (natural-language functional description). This skill calls the hosted Westlake ProTrek Gradio API at `http://www.search-protrek.com`.

## When to use ProTrek vs. other tools

| User intent | Right tool |
|---|---|
| "Find Swiss-Prot proteins whose description mentions heme-binding peroxidase activity" | **ProTrek** (text → sequence) |
| "Annotate this unknown sequence with a free-text functional description" | **ProTrek** (sequence → text) |
| "Find the closest Swiss-Prot homologs of this sequence, semantically" | **ProTrek** (sequence → sequence) |
| "BLAST this sequence against nt/nr or GenBank" | **BLAST** (NCBI), not ProTrek |
| "Find remote/divergent homologs with a profile HMM" | **PHMMER / HMMER**, not ProTrek |
| "Find structural homologs in PDB or AlphaFold DB by 3D shape" | **FoldSeek**, not ProTrek |
| "Cluster sequences with MMseqs2" or "build an MSA" | **MMseqs2 / Clustal**, not ProTrek |
| Search metagenomes (MGnify, OMG) for divergent homology | **Gaia / PHMMER**; ProTrek covers the indexed OMG_prot50/MGnify subsets but is not a metagenome search engine |

ProTrek is strongest when the query is **semantic** ("what does this protein do?") or **cross-modal** (text ↔ sequence ↔ structure). It is UniProt-scoped by design — it will not help with GenBank nucleotide searches or viral protein predictions (disabled by the host).

## Privacy and availability

- Requests go to **third-party infrastructure** at `http://www.search-protrek.com` (hosted by Westlake University). Traffic is plain HTTP.
- No authentication or API key is required as of 2026-04-19 (the same snapshot date as the API probe in `reference/api-reference.md`), but availability, rate limits, and endpoint stability are **not guaranteed**. The service may throttle or go down.
- Do not send proprietary or embargoed sequences if that is a concern. Warn the user before sending sensitive material.
- Viral protein predictions are explicitly blocked by the host for biosecurity reasons.

## Prerequisites

Install `gradio_client` on the fly (no Python project files are bundled with this skill):

```bash
uv run --with gradio_client python - <<'PY'
from gradio_client import Client
client = Client("http://www.search-protrek.com/")
print(client.view_api())
PY
```

Use `Client("http://www.search-protrek.com/")` in all snippets below. The main endpoint is `/search`; pass arguments in the order documented in `reference/api-reference.md`.

## Common modalities (inline)

The three patterns below cover the majority of use cases. For less common pairs (e.g. structure → text, text → structure, using a PDB-file input), **read `reference/modalities.md` and `reference/api-reference.md`** — they document all nine pairwise combinations, the full database list, and the subsection vocabulary for text queries.

### 1. Sequence → sequence (find similar proteins in Swiss-Prot)

Use when the user has an amino-acid sequence and wants semantically similar proteins from UniProt.

```python
from gradio_client import Client

client = Client("http://www.search-protrek.com/")
result = client.predict(
    "MAIKKLVMA...EKRVVE",   # input: amino-acid sequence
    1000,                     # nprobe (1-1_000_000): higher = more accurate, slower
    20,                       # topk (1-100_000): number of hits to return
    "sequence",               # input_type
    "sequence",               # output_type
    "Function",               # subsection_type - ignored for non-text output, but required
    "Swiss-Prot",             # database
    api_name="/search",
)
# result is a 4-tuple: (markdown_summary, download_file, histogram_image, dataframe_of_hits)
hits_markdown, download_file, histogram_png, hits_df = result
print(hits_markdown)
```

### 2. Sequence → function text (annotate an unknown sequence)

Use when the user has an uncharacterized sequence and wants a natural-language functional annotation retrieved from Swiss-Prot.

```python
from gradio_client import Client

client = Client("http://www.search-protrek.com/")
result = client.predict(
    "MSTAGKVIK...LEHHHHHH",   # input: amino-acid sequence
    1000,                      # nprobe
    10,                        # topk
    "sequence",                # input_type
    "text",                    # output_type
    "Function",                # subsection_type - Function is the most common; see reference/api-reference.md for the full list (GO annotation, EC number, Subcellular location, etc.)
    "Swiss-Prot",              # database
    api_name="/search",
)
print(result[0])   # markdown table of candidate functional descriptions
```

### 3. Function text → sequence (natural-language protein discovery)

Use when the user describes a function in English and wants candidate proteins from Swiss-Prot.

```python
from gradio_client import Client

client = Client("http://www.search-protrek.com/")
result = client.predict(
    "Heme-dependent peroxidase active on lignin-derived aromatic compounds, "
    "secreted, thermostable, from a white-rot fungus.",   # natural-language query
    1000,                     # nprobe
    25,                       # topk
    "text",                   # input_type
    "sequence",               # output_type
    "Function",               # subsection_type - required argument even though we're outputting sequences
    "Swiss-Prot",             # database
    api_name="/search",
)
print(result[0])
```

**Tip for text queries:** describe *properties* (activity, cofactor, subcellular location, organism, conditions) rather than an EC number or a single keyword. ProTrek is trained on Swiss-Prot free-text annotation, not on controlled vocabulary alone.

## Less common modalities

Read these reference files on demand:

- `reference/modalities.md` — all 9 pairwise (input x output) modalities with guidance on when each is appropriate, plus structure-input (PDB file) and pairwise similarity scoring.
- `reference/api-reference.md` — endpoint names, exact parameter orders, the full database list (Swiss-Prot, UniRef50, Uncharacterized, OMG_prot50, PDB, GOPC, NCBI, MGnify, OMG), the 31 subsection types, return shapes, and the `/compute_score` endpoint.

When the user asks for anything beyond the three inline modalities — structure input from a PDB file, text → structure, scoring a single input pair, swapping to UniRef50/OMG_prot50/NCBI, or restricting to a specific UniProt subsection — read those reference files before constructing the `gradio_client` call.

## Output handling

Every `/search` call returns a 4-tuple: `(markdown_summary, download_file_path, histogram_image_path, dataframe_of_hits)`. Prefer reporting the markdown summary and the top rows of the dataframe to the user. The histogram is useful for diagnosing score distributions when the top hit score is low.

If the call times out or returns an HTTP error, report it verbatim and suggest retrying with a smaller `topk` or a smaller `nprobe`, or falling back to BLAST/PHMMER/FoldSeek as appropriate to the user's actual intent.
