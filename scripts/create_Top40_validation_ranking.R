# ============================================================
# LUAD Top-40 Biomarker Validation Ranking
# ============================================================

input_file <- "/mnt/d/Cancer_Biomarker_Project/results/validation/LUAD_Top40_DESeq2_validation.csv"

output_file <- "/mnt/d/Cancer_Biomarker_Project/results/validation/LUAD_Top40_final_validation_ranking.csv"

cat("Reading DESeq2 results...\n")

res <- read.csv(
    input_file,
    stringsAsFactors = FALSE
)

# ------------------------------------------------------------
# 1. Calculate absolute effect size
# ------------------------------------------------------------

res$abs_log2FC <- abs(res$log2FoldChange)

# ------------------------------------------------------------
# 2. Validation category
# ------------------------------------------------------------

res$validation_status <- ifelse(
    !is.na(res$padj) &
        res$padj < 0.01 &
        res$abs_log2FC >= 2,
    "Strongly validated",

    ifelse(
        !is.na(res$padj) &
            res$padj < 0.05 &
            res$abs_log2FC >= 1,
        "Validated",

        ifelse(
            !is.na(res$padj) &
                res$padj < 0.05,
            "Weakly validated",
            "Not validated"
        )
    )
)

# ------------------------------------------------------------
# 3. Rank biomarkers
# ------------------------------------------------------------

# Primary ranking: adjusted p-value
# Secondary ranking: absolute log2 fold-change

res <- res[
    order(
        res$padj,
        -res$abs_log2FC,
        na.last = TRUE
    ),
]

res$validation_rank <- seq_len(nrow(res))

# ------------------------------------------------------------
# 4. Reorder columns
# ------------------------------------------------------------

res <- res[
    ,
    c(
        "validation_rank",
        "gene_name",
        "log2FoldChange",
        "abs_log2FC",
        "pvalue",
        "padj",
        "direction",
        "validation_status"
    )
]

# ------------------------------------------------------------
# 5. Save final table
# ------------------------------------------------------------

write.csv(
    res,
    output_file,
    row.names = FALSE
)

# ------------------------------------------------------------
# 6. Summary
# ------------------------------------------------------------

cat("\n============================================\n")
cat("TOP-40 VALIDATION RANKING COMPLETE\n")
cat("============================================\n\n")

cat("Total genes:", nrow(res), "\n\n")

cat("Validation categories:\n")
print(table(res$validation_status))

cat("\nTop 15 biomarkers:\n\n")

print(
    res[
        1:min(15, nrow(res)),
        c(
            "validation_rank",
            "gene_name",
            "log2FoldChange",
            "padj",
            "direction",
            "validation_status"
        )
    ],
    row.names = FALSE
)

cat("\nResults saved to:\n")
cat(output_file, "\n")