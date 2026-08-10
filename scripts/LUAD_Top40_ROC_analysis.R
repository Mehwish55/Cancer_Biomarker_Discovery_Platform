# ============================================================
# LUAD Top-40 Biomarker ROC / AUC Analysis
# Exact 40-gene validation set
# ============================================================

library(DESeq2)
library(pROC)

input_file <- "/mnt/d/Cancer_Biomarker_Project/results/validation/LUAD_Top40_validation_clean.csv"

ranking_file <- "/mnt/d/Cancer_Biomarker_Project/results/validation/LUAD_Top40_final_validation_ranking.csv"

results_file <- "/mnt/d/Cancer_Biomarker_Project/results/validation/LUAD_Top40_ROC_AUC_results.csv"

figure_file <- "/mnt/d/Cancer_Biomarker_Project/figures/LUAD_Top10_ROC_curves.png"

# ------------------------------------------------------------
# 1. Read data
# ------------------------------------------------------------

cat("Reading expression data...\n")

x <- read.csv(
    input_file,
    stringsAsFactors = FALSE
)

# ------------------------------------------------------------
# 2. Read canonical Top-40 genes
# ------------------------------------------------------------

cat("Reading canonical Top-40 gene list...\n")

ranking <- read.csv(
    ranking_file,
    stringsAsFactors = FALSE
)

top40_genes <- unique(
    ranking$gene_name
)

cat("Canonical genes:", length(top40_genes), "\n")

if (length(top40_genes) != 40) {
    stop("ERROR: expected exactly 40 unique genes.")
}

# ------------------------------------------------------------
# 3. Keep only canonical Top-40 genes
# ------------------------------------------------------------

x <- x[
    x$gene_name %in% top40_genes,
    ,
    drop = FALSE
]

# ------------------------------------------------------------
# 4. Create unique gene/sample count combinations
# ------------------------------------------------------------

cat("Constructing count matrix...\n")

x_sum <- aggregate(
    count ~ gene_name + sample_id_y,
    data = x,
    FUN = sum
)

# ------------------------------------------------------------
# 5. Create plain numeric matrix
# ------------------------------------------------------------

gene_levels <- top40_genes

sample_levels <- unique(
    x_sum$sample_id_y
)

counts <- matrix(
    0,
    nrow = length(gene_levels),
    ncol = length(sample_levels),
    dimnames = list(
        gene_levels,
        sample_levels
    )
)

for (i in seq_len(nrow(x_sum))) {

    g <- x_sum$gene_name[i]

    s <- x_sum$sample_id_y[i]

    counts[g, s] <- x_sum$count[i]
}

# Explicitly force base numeric matrix
counts <- matrix(
    as.numeric(counts),
    nrow = nrow(counts),
    ncol = ncol(counts),
    dimnames = dimnames(counts)
)

storage.mode(counts) <- "integer"

cat(
    "Count matrix:",
    nrow(counts),
    "genes x",
    ncol(counts),
    "samples\n"
)

# ------------------------------------------------------------
# 6. Verify exact 40 genes
# ------------------------------------------------------------

if (nrow(counts) != 40) {
    stop(
        paste(
            "ERROR: count matrix contains",
            nrow(counts),
            "genes instead of 40."
        )
    )
}

# ------------------------------------------------------------
# 7. Sample metadata
# ------------------------------------------------------------

sample_ids <- colnames(counts)

condition <- ifelse(
    substr(sample_ids, 14, 15) == "01",
    "Tumor",
    "Normal"
)

condition <- factor(
    condition,
    levels = c("Normal", "Tumor")
)

coldata <- data.frame(
    condition = condition,
    row.names = sample_ids
)

cat(
    "Normal samples:",
    sum(condition == "Normal"),
    "\n"
)

cat(
    "Tumor samples:",
    sum(condition == "Tumor"),
    "\n"
)

# ------------------------------------------------------------
# 8. DESeq2 object
# ------------------------------------------------------------

cat("Creating DESeq2 object...\n")

dds <- DESeqDataSetFromMatrix(
    countData = counts,
    colData = coldata,
    design = ~ condition
)

# ------------------------------------------------------------
# 9. VST normalization
# ------------------------------------------------------------

cat("Running VST normalization...\n")

vsd <- varianceStabilizingTransformation(
    dds,
    blind = TRUE
)

expr <- assay(vsd)

# ------------------------------------------------------------
# 10. ROC analysis
# ------------------------------------------------------------

cat("Running ROC analysis for exactly 40 genes...\n")

genes <- rownames(expr)

roc_results_list <- list()

roc_objects <- list()

for (gene in genes) {

    values <- as.numeric(
        expr[gene, ]
    )

    roc_obj <- roc(
        response = condition,
        predictor = values,
        levels = c("Normal", "Tumor"),
        direction = "<",
        quiet = TRUE
    )

    auc_value <- as.numeric(
        auc(roc_obj)
    )

    ci_auc <- as.numeric(
        ci.auc(
            roc_obj,
            conf.level = 0.95
        )
    )

    best <- coords(
        roc_obj,
        x = "best",
        best.method = "youden",
        ret = c(
            "threshold",
            "sensitivity",
            "specificity"
        ),
        transpose = FALSE
    )

    p_value <- tryCatch(
        {
            roc.test(
                roc_obj,
                auc = 0.5,
                method = "delong"
            )$p.value
        },
        error = function(e) {
            NA_real_
        }
    )

    roc_results_list[[gene]] <- data.frame(
        gene_name = gene,
        AUC = auc_value,
        CI_lower = ci_auc[1],
        CI_upper = ci_auc[3],
        pvalue = p_value,
        sensitivity = as.numeric(best$sensitivity),
        specificity = as.numeric(best$specificity),
        threshold = as.numeric(best$threshold),
        stringsAsFactors = FALSE
    )

    roc_objects[[gene]] <- roc_obj
}

# ------------------------------------------------------------
# 11. Combine results
# ------------------------------------------------------------

roc_results <- do.call(
    rbind,
    roc_results_list
)

rownames(roc_results) <- NULL

# Safety check
roc_results <- roc_results[
    !duplicated(roc_results$gene_name),
    ,
    drop = FALSE
]

if (nrow(roc_results) != 40) {
    stop(
        paste(
            "ERROR: ROC results contain",
            nrow(roc_results),
            "unique genes instead of 40."
        )
    )
}

# ------------------------------------------------------------
# 12. Rank by AUC
# ------------------------------------------------------------

roc_results <- roc_results[
    order(-roc_results$AUC),
    ,
    drop = FALSE
]

roc_results$ROC_rank <- seq_len(
    nrow(roc_results)
)

roc_results <- roc_results[
    ,
    c(
        "ROC_rank",
        "gene_name",
        "AUC",
        "CI_lower",
        "CI_upper",
        "pvalue",
        "sensitivity",
        "specificity",
        "threshold"
    )
]

# ------------------------------------------------------------
# 13. Save results
# ------------------------------------------------------------

write.csv(
    roc_results,
    results_file,
    row.names = FALSE
)

# ------------------------------------------------------------
# 14. Plot Top-10 ROC curves
# ------------------------------------------------------------

top10 <- roc_results$gene_name[1:10]

png(
    figure_file,
    width = 2400,
    height = 2000,
    res = 300
)

plot(
    roc_objects[[top10[1]]],
    main = "Top-10 LUAD Biomarker ROC Curves",
    legacy.axes = TRUE,
    print.auc = FALSE
)

for (gene in top10[-1]) {

    plot(
        roc_objects[[gene]],
        add = TRUE,
        print.auc = FALSE
    )
}

legend_labels <- paste0(
    top10,
    " (AUC=",
    sprintf(
        "%.3f",
        roc_results$AUC[
            match(
                top10,
                roc_results$gene_name
            )
        ]
    ),
    ")"
)

legend(
    "bottomright",
    legend = legend_labels,
    lty = 1,
    cex = 0.8
)

dev.off()

# ------------------------------------------------------------
# 15. Final summary
# ------------------------------------------------------------

cat("\n============================================\n")
cat("ROC/AUC ANALYSIS COMPLETE\n")
cat("============================================\n")

cat(
    "Genes analyzed:",
    nrow(roc_results),
    "\n"
)

cat(
    "Unique genes:",
    length(unique(roc_results$gene_name)),
    "\n"
)

cat("\nTop 15 biomarkers by AUC:\n\n")

print(
    roc_results[
        1:15,
        c(
            "ROC_rank",
            "gene_name",
            "AUC",
            "CI_lower",
            "CI_upper",
            "sensitivity",
            "specificity"
        )
    ],
    row.names = FALSE
)

cat("\nResults saved to:\n")
cat(results_file, "\n")

cat("\nROC figure saved to:\n")
cat(figure_file, "\n")