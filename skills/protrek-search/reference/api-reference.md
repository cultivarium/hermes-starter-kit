# ProTrek Gradio API reference

Base URL: `http://www.search-protrek.com/`  
Gradio version: 4.37.1  
Client library: `gradio_client` (install via `uv run --with gradio_client python - <<...` — no auth, no API key).

All endpoints are invoked via `client.predict(..., api_name="/<endpoint>")`.

---

## `/search` (primary endpoint)

The main retrieval endpoint. Takes 7 positional arguments in this order:

| # | Name | Type | Notes |
|---|---|---|---|
| 1 | `input` | `str` | The query string. Amino-acid sequence (for `input_type="sequence"`), Foldseek 3Di string (`"structure"`), or free-text description (`"text"`). |
| 2 | `nprobe` | `int` | Number of clusters to search. Valid range 1–1,000,000. Default 1000. Higher = more accurate, slower. |
| 3 | `topk` | `int` | Number of hits to return. Valid range 1–100,000. Default 5. |
| 4 | `input_type` | `str` | One of `"sequence"`, `"structure"`, `"text"`. |
| 5 | `output_type` | `str` | One of `"sequence"`, `"structure"`, `"text"`. |
| 6 | `subsection_type` | `str` | UniProt annotation subsection. Only meaningful when `output_type="text"`. Required for all calls (pass `"Function"` as default). See enum below. |
| 7 | `database` | `str` | One of: `"Swiss-Prot"`, `"UniRef50"`, `"Uncharacterized"`, `"OMG_prot50"`, `"PDB"`, `"GOPC"`, `"NCBI"`, `"MGnify"`, `"OMG"`. Default `"Swiss-Prot"`. The UI dynamically narrows this list based on `output_type`; if a (output_type, database) combination errors, try `"Swiss-Prot"`. |

### Return shape

A 4-tuple:

| # | Contents |
|---|---|
| 0 | `str` — markdown summary of results (human-readable; report this to the user) |
| 1 | file path — downloadable results file (CSV/TSV) |
| 2 | file path — PNG histogram of match scores |
| 3 | `list[list]` or `dict` — raw dataframe of hits (columns include rank, accession, score, and — for text output — the annotation string) |

### Subsection type enum (31 values)

`Activity regulation`, `Allergenic properties`, `Biophysicochemical properties`, `Biotechnology`, `Catalytic activity`, `Caution`, `Cofactor`, `Developmental stage`, `Disruption phenotype`, `Domain (non-positional annotation)`, `Enzyme commission number`, `Function`, `GO annotation`, `Gene names`, `Global`, `Induction`, `Involvement in disease`, `Miscellaneous`, `Organism`, `Pathway`, `Pharmaceutical use`, `Polymorphism`, `Post-translational modification`, `Protein names`, `Proteomes`, `RNA Editing`, `Sequence similarities`, `Subcellular location`, `Subunit`, `Tissue specificity`, `Toxic dose`.

---

## `/compute_score`

Compute similarity between two specific inputs of any modality. 4 positional arguments:

| # | Name | Type | Notes |
|---|---|---|---|
| 1 | `input1_type` | `str` | `"sequence"`, `"structure"`, or `"text"` |
| 2 | `input1` | `str` | First query string |
| 3 | `input2_type` | `str` | `"sequence"`, `"structure"`, or `"text"` |
| 4 | `input2` | `str` | Second query string |

Returns a similarity score (gradio `Label` — typically a dict with `label` and `confidences`, or a plain float depending on client version).

---

## `/parse_pdb_file`, `/parse_pdb_file_1`, `/parse_pdb_file_2`

Convert a PDB/CIF file + chain to a Foldseek 3Di string so it can be used as a `"structure"` input to `/search` or `/compute_score`. 3 positional arguments:

| # | Name | Type | Notes |
|---|---|---|---|
| 1 | `input_type` | `str` | Usually `"structure"` |
| 2 | `pdb_file` | `FileData` (`gradio_client.handle_file(...)`) | Upload handle for the local PDB/CIF file |
| 3 | `chain` | `str` | Chain ID to extract (default `"A"`) |

Returns the Foldseek 3Di string as a single string.

The three variants (`parse_pdb_file`, `parse_pdb_file_1`, `parse_pdb_file_2`) are aliases bound to different UI panels; use `parse_pdb_file` unless you have reason to pick one of the others.

---

## Other auxiliary endpoints (rarely useful from a client)

These exist in the API surface but are intended for the Gradio UI to update dependent widgets. Generally safe to ignore from a scripted client:

- `/change_input_type`, `/change_output_type`, `/change_db_type` — update dependent dropdowns in the UI.
- `/load_example`, `/load_example_1` — populate example inputs.
- `/clear_results` — clear the current result panel.
- `/change_input_type_1`, `/change_input_type_2` — variants for the compute-score panel inputs.

---

## Database enum (full list, as of 2025-10-02)

`Swiss-Prot`, `UniRef50`, `Uncharacterized`, `OMG_prot50`, `PDB`, `GOPC`, `NCBI`, `MGnify`, `OMG`.

Note: the UI dynamically restricts valid (output_type, database) pairs. If a call errors with a database-not-available message, fall back to `"Swiss-Prot"`.

---

## Error handling

- The host may return HTTP errors under load. Report the error verbatim and retry with smaller `topk` / `nprobe`, or suggest a different tool (BLAST / PHMMER / FoldSeek) if the user's intent is a better fit there.
- Viral protein inputs are explicitly rejected by the server for biosecurity reasons.
- Endpoint names, parameter orders, and the database list were verified via `gradio_client.Client("http://www.search-protrek.com/").view_api()` on 2026-04-19. Re-run the probe if the API appears to have drifted.
