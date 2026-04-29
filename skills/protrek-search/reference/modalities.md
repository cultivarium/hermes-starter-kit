# ProTrek modalities

ProTrek supports pairwise retrieval across three modalities (sequence, structure, text) for a total of 9 input × output combinations. The three most common are documented inline in `SKILL.md`; this file covers the rest and the auxiliary endpoints.

All examples use the same base client:

```python
from gradio_client import Client
client = Client("http://www.search-protrek.com/")
```

The `/search` endpoint signature (in order, positional):

```
input, nprobe, topk, input_type, output_type, subsection_type, database
```

See `api-reference.md` for the exact parameter definitions and valid value enums.

---

## The 9 pairwise modalities

| Input modality | Output modality | Inline in SKILL.md? | Use case |
|---|---|---|---|
| sequence | sequence | Yes | Find semantically similar proteins to a query amino-acid sequence |
| sequence | structure | No (see below) | Find proteins whose 3D structure matches what you'd expect for this sequence |
| sequence | text | Yes | Annotate an unknown sequence with free-text functional descriptions |
| structure | sequence | No (see below) | Given a structure (PDB or Foldseek 3Di), find sequence-level homologs |
| structure | structure | No (see below) | Given a structure, find structurally similar entries (use **FoldSeek** for large-scale structure DB search) |
| structure | text | No (see below) | Annotate an unknown structure with free-text functional descriptions |
| text | sequence | Yes | Natural-language protein discovery ("find a thermostable laccase...") |
| text | structure | No (see below) | Retrieve structures matching a natural-language description |
| text | text | No (see below) | Cluster annotations by semantic similarity (rarely useful; usually structure ↔ sequence is what you want) |

### When each non-inline modality is the right call

- **structure → sequence / structure → text**: the user has a PDB/CIF file of an uncharacterized protein and wants sequence hits or functional annotation. Use `/parse_pdb_file` first to extract the Foldseek 3Di string (see below), then call `/search` with `input_type="structure"`.
- **sequence → structure / text → structure**: the user wants candidate 3D structures that would match a sequence or description. Output `"structure"` returns Foldseek 3Di strings paired with the UniProt accession — the actual PDB/AlphaFold model must be fetched separately.
- **text → text**: rarely the right tool. If the user wants to find similar annotations, use a standard text-search tool or embedding search. Only reach for ProTrek text→text when you specifically want ProTrek's learned protein-description embeddings.

---

## Structure input from a PDB/CIF file

To search using a structure input, first convert the PDB file to Foldseek 3Di via `/parse_pdb_file` (or `/parse_pdb_file_1` / `/parse_pdb_file_2` for the alternate UI panels):

```python
from gradio_client import Client, handle_file

client = Client("http://www.search-protrek.com/")
foldseek_string = client.predict(
    "structure",                                 # input_type (the radio on the UI)
    handle_file("/path/to/protein.pdb"),          # pdb_file (FileData)
    "A",                                          # chain to extract
    api_name="/parse_pdb_file",
)

# Now search using the extracted 3Di string as a structure input
result = client.predict(
    foldseek_string,
    1000,
    10,
    "structure",     # input_type
    "sequence",      # output_type: change to "text" for functional annotation
    "Function",
    "Swiss-Prot",
    api_name="/search",
)
print(result[0])
```

`/parse_pdb_file` returns the Foldseek 3Di sequence string; feed that directly as the `input` argument to `/search`.

---

## Pairwise similarity scoring (`/compute_score`)

For two specific proteins (any pair of modalities), ProTrek exposes a direct similarity score. This is useful for validating a cross-modal match without a full database scan.

```python
score = client.predict(
    "sequence",                                   # input1_type
    "MAIKKLVMA...EKRVVE",                          # input1
    "text",                                       # input2_type
    "Heme-dependent peroxidase, secreted.",        # input2
    api_name="/compute_score",
)
print(score)   # float-like similarity score (higher = more similar)
```

Valid input types: `sequence`, `structure` (Foldseek 3Di string), `text`.

---

## Subsection filtering (only meaningful when output_type="text")

When retrieving text annotations, the `subsection_type` argument constrains which UniProt annotation section the candidate descriptions come from. The default is `"Function"`, which is almost always the right choice. See `api-reference.md` for the full list of 31 subsection types (GO annotation, Enzyme commission number, Subcellular location, Pathway, etc.).

When `output_type` is `"sequence"` or `"structure"`, pass `subsection_type="Function"` — it is a required positional argument but is ignored by the server for non-text output.

---

## Choosing the database

| Database | What's in it | When to use |
|---|---|---|
| `Swiss-Prot` | UniProtKB/Swiss-Prot (reviewed, manually annotated, ~570K proteins) | **Default.** Highest-quality annotations; use for most semantic searches. |
| `UniRef50` | UniRef50 clusters (~60M+ proteins at 50% identity) | Broader coverage including unreviewed TrEMBL; use when Swiss-Prot returns nothing |
| `Uncharacterized` | UniProt entries labeled "uncharacterized" | When deliberately looking for proteins with no annotation |
| `OMG_prot50` | Open Microbial Genomes, 50% identity clusters | Metagenome-scale microbial diversity |
| `PDB` | Protein Data Bank | Structure-anchored search — but for pure structure→structure, prefer **FoldSeek** |
| `GOPC` | Gene Ontology-sourced Protein Clusters | GO-term-anchored search |
| `NCBI` | NCBI RefSeq/nr subset indexed by ProTrek | Broad taxonomic coverage |
| `MGnify` | EBI MGnify metagenome-assembled proteins | Environmental metagenomes |
| `OMG` | Open Microbial Genomes (full, not clustered) | Microbial metagenomes at full resolution |

If the user asks for "all available databases" or doesn't specify, default to **Swiss-Prot**. Call `/search` once per database if breadth is needed.
