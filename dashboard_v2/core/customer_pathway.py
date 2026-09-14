from __future__ import annotations

from typing import Any
import re
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


class CustomerPathwayError(ValueError):
    """Raised when customer pathway analysis cannot be completed."""


EXPECTED_COLUMNS = [
    "GOID",
    "TERM",
    "ONTOLOGY",
    "Hits",
    "TermSize",
    "GeneRatio",
    "BgRatio",
    "FoldEnrichment",
    "pvalue",
    "padj",
    "contributing_genes",
]


def _empty_result() -> dict[str, Any]:
    empty = pd.DataFrame(columns=EXPECTED_COLUMNS)

    return {
        "BP": empty.copy(),
        "CC": empty.copy(),
        "MF": empty.copy(),
        "KEGG": pd.DataFrame(),
        "mapping": pd.DataFrame(),
        "background_size": 0,
        "candidate_size": 0,
        "input_background_size": 0,
        "input_candidate_size": 0,
        "unmapped_background": 0,
        "unmapped_candidate": 0,
    }


def _require_r_packages() -> None:
    packages = [
        "org.Hs.eg.db",
        "AnnotationDbi",
        "GO.db",
    ]

    missing = []

    for package in packages:
        result = subprocess.run(
            [
                "Rscript",
                "-e",
                f"cat(requireNamespace('{package}', quietly=TRUE))",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stdout.strip().lower() != "true":
            missing.append(package)

    if missing:
        raise CustomerPathwayError(
            "Missing R/Bioconductor packages: "
            + ", ".join(missing)
        )


def _detect_gene_column(df: pd.DataFrame, preferred: str | None = None) -> str:
    if preferred and preferred in df.columns:
        return preferred

    normalized = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    candidates = [
        "gene",
        "gene_id",
        "geneid",
        "gene_symbol",
        "symbol",
        "genes",
        "ensembl",
        "ensembl_id",
        "entrez",
        "entrez_id",
    ]

    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]

    raise CustomerPathwayError(
        "Could not identify the gene column. "
        "Expected a column such as Gene, Gene_ID, Symbol, "
        "Ensembl, or Entrez."
    )


def _clean_gene_ids(series: pd.Series) -> list[str]:
    values = (
        series.dropna()
        .astype(str)
        .str.strip()
    )

    values = values[values != ""]
    values = values[values.str.lower() != "nan"]

    # Remove Ensembl version suffixes, e.g. ENSG00000141510.17
    values = values.str.replace(
        r"\.\d+$",
        "",
        regex=True,
    )

    return sorted(set(values.tolist()))


def _run_r_enrichment(
    background_genes: list[str],
    candidate_genes: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:

    with tempfile.TemporaryDirectory(prefix="onconexa_pathway_") as tmp:
        tmpdir = Path(tmp)

        background_file = tmpdir / "background.txt"
        candidate_file = tmpdir / "candidate.txt"
        result_file = tmpdir / "results.csv"
        mapping_file = tmpdir / "mapping.csv"
        stats_file = tmpdir / "stats.csv"
        script_file = tmpdir / "run_enrichment.R"

        pd.Series(background_genes).to_csv(
            background_file,
            index=False,
            header=False,
        )

        pd.Series(candidate_genes).to_csv(
            candidate_file,
            index=False,
            header=False,
        )

        r_script = r'''
suppressPackageStartupMessages({
    library(org.Hs.eg.db)
    library(AnnotationDbi)
    library(GO.db)
})

background_input <- unique(trimws(readLines("BACKGROUND_FILE")))
candidate_input <- unique(trimws(readLines("CANDIDATE_FILE")))

background_input <- background_input[
    background_input != "" &
    !is.na(background_input)
]

candidate_input <- candidate_input[
    candidate_input != "" &
    !is.na(candidate_input)
]


# ------------------------------------------------------------
# Detect identifier type and map to ENTREZID
# ------------------------------------------------------------

detect_keytype <- function(ids) {

    if (length(ids) == 0) {
        return("SYMBOL")
    }

    sample_ids <- head(ids, 100)

    if (all(grepl("^ENSG[0-9]+$", sample_ids, ignore.case=TRUE))) {
        return("ENSEMBL")
    }

    if (all(grepl("^[0-9]+$", sample_ids))) {
        return("ENTREZID")
    }

    return("SYMBOL")
}


map_ids <- function(ids) {

    if (length(ids) == 0) {
        return(data.frame())
    }

    keytype <- detect_keytype(ids)

    mapped <- tryCatch(
        AnnotationDbi::select(
            org.Hs.eg.db,
            keys=ids,
            keytype=keytype,
            columns=c(
                "SYMBOL",
                "ENTREZID",
                "ENSEMBL"
            )
        ),
        error=function(e) {
            data.frame()
        }
    )

    if (nrow(mapped) == 0) {
        return(data.frame())
    }

    mapped <- mapped[
        !is.na(mapped$ENTREZID) &
        mapped$ENTREZID != "",
        ,
        drop=FALSE
    ]

    mapped <- mapped[
        !duplicated(mapped[, c(keytype, "ENTREZID")]),
        ,
        drop=FALSE
    ]

    mapped
}


background_map <- map_ids(background_input)
candidate_map <- map_ids(candidate_input)


if (nrow(background_map) == 0) {
    write.csv(
        data.frame(),
        "RESULT_FILE",
        row.names=FALSE
    )

    write.csv(
        data.frame(),
        "MAPPING_FILE",
        row.names=FALSE
    )

    write.csv(
        data.frame(
            background_input=length(background_input),
            candidate_input=length(candidate_input),
            background_mapped=0,
            candidate_mapped=0
        ),
        "STATS_FILE",
        row.names=FALSE
    )

    quit(save="no", status=0)
}


background_ids <- unique(background_map$ENTREZID)


# Candidate genes must be members of the uploaded background.
candidate_ids <- unique(
    candidate_map$ENTREZID[
        candidate_map$ENTREZID %in% background_ids
    ]
)


# ------------------------------------------------------------
# GO annotation
# ------------------------------------------------------------

go_annotation <- tryCatch(
    AnnotationDbi::select(
        org.Hs.eg.db,
        keys=background_ids,
        keytype="ENTREZID",
        columns=c(
            "GO",
            "ONTOLOGY"
        )
    ),
    error=function(e) {
        data.frame()
    }
)


go_annotation <- go_annotation[
    !is.na(go_annotation$GO) &
    !is.na(go_annotation$ONTOLOGY),
    ,
    drop=FALSE
]


# Remove duplicated gene-term associations.
go_annotation <- unique(
    go_annotation[, c(
        "ENTREZID",
        "GO",
        "ONTOLOGY"
    )]
)


if (nrow(go_annotation) == 0 || length(candidate_ids) == 0) {

    write.csv(
        data.frame(),
        "RESULT_FILE",
        row.names=FALSE
    )

    write.csv(
        rbind(
            background_map,
            candidate_map
        ),
        "MAPPING_FILE",
        row.names=FALSE
    )

    write.csv(
        data.frame(
            background_input=length(background_input),
            candidate_input=length(candidate_input),
            background_mapped=length(background_ids),
            candidate_mapped=length(candidate_ids)
        ),
        "STATS_FILE",
        row.names=FALSE
    )

    quit(save="no", status=0)
}


N <- length(background_ids)
n <- length(candidate_ids)


run_go <- function(ontology) {

    go <- go_annotation[
        go_annotation$ONTOLOGY == ontology,
        ,
        drop=FALSE
    ]

    if (nrow(go) == 0) {
        return(data.frame())
    }

    background_counts <- table(go$GO)

    candidate_go <- go[
        go$ENTREZID %in% candidate_ids,
        ,
        drop=FALSE
    ]

    if (nrow(candidate_go) == 0) {
        return(data.frame())
    }

    hit_counts <- table(candidate_go$GO)

    terms <- intersect(
        names(hit_counts),
        names(background_counts)
    )

    if (length(terms) == 0) {
        return(data.frame())
    }

    rows <- lapply(
        terms,
        function(term) {

            K <- as.integer(background_counts[[term]])
            k <- as.integer(hit_counts[[term]])

            if (K <= 0 || k <= 0 || K > N || k > n) {
                return(NULL)
            }

            pvalue <- phyper(
                k - 1,
                K,
                N - K,
                n,
                lower.tail=FALSE
            )

            candidate_term_genes <- candidate_go$ENTREZID[
                candidate_go$GO == term
            ]

            symbols <- unique(
                candidate_map$SYMBOL[
                    candidate_map$ENTREZID %in%
                    candidate_term_genes
                ]
            )

            term_name <- tryCatch(
                AnnotationDbi::select(
                    GO.db,
                    keys=term,
                    keytype="GOID",
                    columns="TERM"
                )$TERM[1],
                error=function(e) NA_character_
            )

            if (is.na(term_name) || term_name == "") {
                term_name <- term
            }

            data.frame(
                GOID=term,
                TERM=term_name,
                ONTOLOGY=ontology,
                Hits=k,
                TermSize=K,
                GeneRatio=k / n,
                BgRatio=K / N,
                FoldEnrichment=(k / n) / (K / N),
                pvalue=pvalue,
                contributing_genes=paste(
                    symbols,
                    collapse=", "
                ),
                stringsAsFactors=FALSE
            )
        }
    )

    rows <- Filter(
        Negate(is.null),
        rows
    )

    if (length(rows) == 0) {
        return(data.frame())
    }

    out <- do.call(rbind, rows)

    out$padj <- p.adjust(
        out$pvalue,
        method="BH"
    )

    out <- out[
        order(
            out$padj,
            -out$FoldEnrichment
        ),
        ,
        drop=FALSE
    ]

    out
}


bp <- run_go("BP")
cc <- run_go("CC")
mf <- run_go("MF")


go_results <- rbind(
    bp,
    cc,
    mf
)


# ------------------------------------------------------------
# Mapping/provenance
# ------------------------------------------------------------

mapping <- rbind(
    background_map,
    candidate_map
)

mapping <- unique(mapping)


write.csv(
    go_results,
    "RESULT_FILE",
    row.names=FALSE
)

write.csv(
    mapping,
    "MAPPING_FILE",
    row.names=FALSE
)

write.csv(
    data.frame(
        background_input=length(background_input),
        candidate_input=length(candidate_input),
        background_mapped=length(background_ids),
        candidate_mapped=length(candidate_ids)
    ),
    "STATS_FILE",
    row.names=FALSE
)
'''

        r_script = (
            r_script
            .replace("BACKGROUND_FILE", str(background_file))
            .replace("CANDIDATE_FILE", str(candidate_file))
            .replace("RESULT_FILE", str(result_file))
            .replace("MAPPING_FILE", str(mapping_file))
            .replace("STATS_FILE", str(stats_file))
        )

        script_file.write_text(
            r_script,
            encoding="utf-8",
        )

        completed = subprocess.run(
            [
                "Rscript",
                str(script_file),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if completed.returncode != 0:
            raise CustomerPathwayError(
                "R pathway enrichment failed:\n\n"
                + completed.stderr[-4000:]
            )

        results = (
            pd.read_csv(result_file)
            if result_file.exists() and result_file.stat().st_size > 0
            else pd.DataFrame()
        )

        mapping = (
            pd.read_csv(mapping_file)
            if mapping_file.exists() and mapping_file.stat().st_size > 0
            else pd.DataFrame()
        )

        stats = (
            pd.read_csv(stats_file)
            if stats_file.exists() and stats_file.stat().st_size > 0
            else pd.DataFrame()
        )

        if stats.empty:
            counts = {
                "background_input": len(background_genes),
                "candidate_input": len(candidate_genes),
                "background_mapped": 0,
                "candidate_mapped": 0,
            }
        else:
            row = stats.iloc[0]
            counts = {
                "background_input": int(row["background_input"]),
                "candidate_input": int(row["candidate_input"]),
                "background_mapped": int(row["background_mapped"]),
                "candidate_mapped": int(row["candidate_mapped"]),
            }

        return results, mapping, counts


def run_customer_go_enrichment(
    expression_data: pd.DataFrame,
    differential_expression: pd.DataFrame,
    gene_column: str | None = None,
) -> dict[str, Any]:

    if expression_data is None or expression_data.empty:
        raise CustomerPathwayError(
            "Uploaded expression data is empty."
        )

    if differential_expression is None or differential_expression.empty:
        raise CustomerPathwayError(
            "Differential-expression results are empty."
        )

    expression_gene_column = _detect_gene_column(
        expression_data,
        gene_column,
    )

    de_gene_column = _detect_gene_column(
        differential_expression,
        "gene",
    )

    background_genes = _clean_gene_ids(
        expression_data[expression_gene_column]
    )

    candidate_genes = _clean_gene_ids(
        differential_expression[de_gene_column]
    )

    if len(background_genes) < 2:
        raise CustomerPathwayError(
            "At least two genes are required in the uploaded "
            "expression background."
        )

    if len(candidate_genes) == 0:
        raise CustomerPathwayError(
            "No differential-expression candidate genes were found."
        )

    _require_r_packages()

    results, mapping, counts = _run_r_enrichment(
        background_genes,
        candidate_genes,
    )

    empty = pd.DataFrame(columns=EXPECTED_COLUMNS)

    if results.empty:
        return {
            "BP": empty.copy(),
            "CC": empty.copy(),
            "MF": empty.copy(),
            "KEGG": pd.DataFrame(),
            "mapping": mapping,
            "background_size": counts["background_mapped"],
            "candidate_size": counts["candidate_mapped"],
            "input_background_size": counts["background_input"],
            "input_candidate_size": counts["candidate_input"],
            "unmapped_background": (
                counts["background_input"]
                - counts["background_mapped"]
            ),
            "unmapped_candidate": (
                counts["candidate_input"]
                - counts["candidate_mapped"]
            ),
        }

    for column in [
        "Hits",
        "TermSize",
        "GeneRatio",
        "BgRatio",
        "FoldEnrichment",
        "pvalue",
        "padj",
    ]:
        if column in results.columns:
            results[column] = pd.to_numeric(
                results[column],
                errors="coerce",
            )

    return {
        "BP": results[
            results["ONTOLOGY"] == "BP"
        ].reset_index(drop=True),
        "CC": results[
            results["ONTOLOGY"] == "CC"
        ].reset_index(drop=True),
        "MF": results[
            results["ONTOLOGY"] == "MF"
        ].reset_index(drop=True),
        "KEGG": pd.DataFrame(),
        "mapping": mapping,
        "background_size": counts["background_mapped"],
        "candidate_size": counts["candidate_mapped"],
        "input_background_size": counts["background_input"],
        "input_candidate_size": counts["candidate_input"],
        "unmapped_background": (
            counts["background_input"]
            - counts["background_mapped"]
        ),
        "unmapped_candidate": (
            counts["candidate_input"]
            - counts["candidate_mapped"]
        ),
    }
