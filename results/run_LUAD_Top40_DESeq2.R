library(DESeq2)

input_file <- "/mnt/d/Cancer_Biomarker_Project/results/validation/LUAD_Top40_validation_clean.csv"
output_file <- "/mnt/d/Cancer_Biomarker_Project/results/validation/LUAD_Top40_DESeq2_validation.csv"

cat("Reading input file...\n")

x <- read.csv(input_file, stringsAsFactors = FALSE)

cat("Rows:", nrow(x), "\n")
cat("Unique genes:", length(unique(x[["gene_name"]])), "\n")
cat("Unique samples:", length(unique(x[["sample_id_y"]])), "\n")

# --------------------------------------------------
# 1. Create sample type
# --------------------------------------------------

sample_ids <- unique(x[["sample_id_y"]])

sample_type <- ifelse(
    substr(sample_ids, 14, 15) == "01",
    "Tumor",
    ifelse(
        substr(sample_ids, 14, 15) == "11",
        "Normal",
        "Other"
    )
)

cat("\nSample types:\n")
print(table(sample_type))

# --------------------------------------------------
# 2. Create count matrix
# --------------------------------------------------

cat("\nCreating count matrix...\n")

tab <- xtabs(
    count ~ gene_name + sample_id_y,
    data = x
)

# Explicitly create a NEW plain numeric matrix
counts <- matrix(
    as.numeric(tab),
    nrow = nrow(tab),
    ncol = ncol(tab)
)

rownames(counts) <- rownames(tab)
colnames(counts) <- colnames(tab)

cat("Count matrix dimensions:\n")
print(dim(counts))

cat("Class of counts object:\n")
print(class(counts))

cat("Storage mode:\n")
print(storage.mode(counts))

# --------------------------------------------------
# 3. Sample metadata
# --------------------------------------------------

condition <- ifelse(
    substr(colnames(counts), 14, 15) == "01",
    "Tumor",
    "Normal"
)

coldata <- data.frame(
    condition = factor(
        condition,
        levels = c("Normal", "Tumor")
    ),
    row.names = colnames(counts)
)

cat("\nMetadata:\n")
print(table(coldata$condition))

# --------------------------------------------------
# 4. DESeq2 dataset
# --------------------------------------------------

cat("\nCreating DESeqDataSet...\n")

dds <- DESeqDataSetFromMatrix(
    countData = round(counts),
    colData = coldata,
    design = ~ condition
)

cat("DESeqDataSet successfully created.\n")

# --------------------------------------------------
# 5. Run DESeq2
# --------------------------------------------------

cat("\nRunning DESeq2...\n")

dds <- DESeq(
    dds,
    quiet = TRUE
)

cat("DESeq2 completed successfully.\n")

# --------------------------------------------------
# 6. Extract results
# --------------------------------------------------

res <- results(
    dds,
    contrast = c("condition", "Tumor", "Normal")
)

res <- as.data.frame(res)

res[["gene_name"]] <- rownames(res)

res <- res[
    ,
    c(
        "gene_name",
        "baseMean",
        "log2FoldChange",
        "lfcSE",
        "stat",
        "pvalue",
        "padj"
    )
]

# --------------------------------------------------
# 7. Direction
# --------------------------------------------------

res[["direction"]] <- ifelse(
    res[["log2FoldChange"]] > 0,
    "Up in Tumor",
    "Down in Tumor"
)

# --------------------------------------------------
# 8. Sort results
# --------------------------------------------------

res <- res[
    order(
        res[["padj"]],
        -abs(res[["log2FoldChange"]])
    ),
]

# --------------------------------------------------
# 9. Save results
# --------------------------------------------------

write.csv(
    res,
    output_file,
    row.names = FALSE
)

# --------------------------------------------------
# 10. Summary
# --------------------------------------------------

cat("\n====================================\n")
cat("ANALYSIS COMPLETE\n")
cat("====================================\n")

cat("Genes analyzed:", nrow(res), "\n")

cat(
    "Significant FDR < 0.05:",
    sum(!is.na(res[["padj"]]) & res[["padj"]] < 0.05),
    "\n"
)

cat(
    "Significant FDR < 0.01:",
    sum(!is.na(res[["padj"]]) & res[["padj"]] < 0.01),
    "\n"
)

cat("\nTop results:\n")

print(
    res[
        ,
        c(
            "gene_name",
            "log2FoldChange",
            "pvalue",
            "padj",
            "direction"
        )
    ]
)

cat("\nResults saved to:\n")
cat(output_file, "\n")