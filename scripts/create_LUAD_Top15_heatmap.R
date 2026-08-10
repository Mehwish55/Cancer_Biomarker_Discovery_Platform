# ============================================================
# LUAD Top-15 Biomarker Validation Heatmap
# ============================================================

library(DESeq2)
library(pheatmap)

input_file <- "/mnt/d/Cancer_Biomarker_Project/results/validation/LUAD_Top40_validation_clean.csv"

output_file <- "/mnt/d/Cancer_Biomarker_Project/figures/LUAD_Top15_biomarker_heatmap.png"

# ------------------------------------------------------------
# 1. Read data
# ------------------------------------------------------------

cat("Reading data...\n")

x <- read.csv(
    input_file,
    stringsAsFactors = FALSE
)

# ------------------------------------------------------------
# 2. Create count matrix
# ------------------------------------------------------------

tab <- xtabs(
    count ~ gene_name + sample_id_y,
    data = x
)

counts <- matrix(
    as.numeric(tab),
    nrow = nrow(tab),
    ncol = ncol(tab),
    dimnames = dimnames(tab)
)

# ------------------------------------------------------------
# 3. Sample metadata
# ------------------------------------------------------------

sample_ids <- colnames(counts)

condition <- ifelse(
    substr(sample_ids, 14, 15) == "01",
    "Tumor",
    "Normal"
)

coldata <- data.frame(
    condition = factor(
        condition,
        levels = c("Normal", "Tumor")
    ),
    row.names = sample_ids
)

# ------------------------------------------------------------
# 4. Create DESeq2 object
# ------------------------------------------------------------

dds <- DESeqDataSetFromMatrix(
    countData = round(counts),
    colData = coldata,
    design = ~ condition
)

# ------------------------------------------------------------
# 5. Variance stabilizing transformation
# ------------------------------------------------------------

cat("Running VST normalization...\n")

vsd <- varianceStabilizingTransformation(
    dds,
    blind = TRUE
)

vsd_matrix <- assay(vsd)

# ------------------------------------------------------------
# 6. Select Top-15 genes
# ------------------------------------------------------------

top15 <- c(
    "PYCR1",
    "FAM83A",
    "B3GNT3",
    "CRABP2",
    "COL11A1",
    "ABCA12",
    "CYP24A1",
    "PPP1R14D",
    "MYEOV",
    "PITX2",
    "TMPRSS11E",
    "EEF1A2",
    "TRPM8",
    "PRAME",
    "MMP11"
)

# Keep only genes present in matrix
top15 <- top15[top15 %in% rownames(vsd_matrix)]

cat("Genes included:", length(top15), "\n")

# ------------------------------------------------------------
# 7. Extract expression matrix
# ------------------------------------------------------------

heatmap_matrix <- vsd_matrix[top15, ]

# ------------------------------------------------------------
# 8. Z-score each gene
# ------------------------------------------------------------

heatmap_matrix <- t(
    scale(
        t(heatmap_matrix)
    )
)

# ------------------------------------------------------------
# 9. Order samples: Normal first, Tumor second
# ------------------------------------------------------------

sample_order <- order(
    coldata$condition
)

heatmap_matrix <- heatmap_matrix[
    ,
    sample_order
]

annotation_col <- data.frame(
    Condition = coldata$condition[sample_order]
)

rownames(annotation_col) <- colnames(heatmap_matrix)

# ------------------------------------------------------------
# 10. Create output directory
# ------------------------------------------------------------

dir.create(
    "/mnt/d/Cancer_Biomarker_Project/figures",
    showWarnings = FALSE,
    recursive = TRUE
)

# ------------------------------------------------------------
# 11. Save high-resolution heatmap
# ------------------------------------------------------------

png(
    filename = output_file,
    width = 2400,
    height = 1800,
    res = 300
)

pheatmap(
    heatmap_matrix,
    annotation_col = annotation_col,
    cluster_rows = TRUE,
    cluster_cols = TRUE,
    show_colnames = FALSE,
    fontsize_row = 10,
    main = "LUAD Top-15 Validated Biomarkers",
    border_color = NA
)

dev.off()

cat("\n====================================\n")
cat("HEATMAP COMPLETE\n")
cat("====================================\n")

cat("Genes:", length(top15), "\n")
cat("Samples:", ncol(heatmap_matrix), "\n")
cat("Normal samples:", sum(coldata$condition == "Normal"), "\n")
cat("Tumor samples:", sum(coldata$condition == "Tumor"), "\n")

cat("\nSaved to:\n")
cat(output_file, "\n")