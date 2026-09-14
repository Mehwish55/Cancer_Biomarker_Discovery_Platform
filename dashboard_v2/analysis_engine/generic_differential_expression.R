#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 4) {
  stop(
    paste(
      "Usage:",
      "Rscript generic_differential_expression.R",
      "<expression_csv>",
      "<metadata_csv>",
      "<expression_type>",
      "<output_csv>"
    )
  )
}

expression_file <- args[1]
metadata_file <- args[2]
expression_type <- tolower(args[3])
output_file <- args[4]

suppressPackageStartupMessages({
  library(limma)
  library(DESeq2)
})

# ------------------------------------------------------------
# Read input data
# ------------------------------------------------------------

expression_df <- read.csv(
  expression_file,
  check.names = FALSE,
  stringsAsFactors = FALSE
)

metadata_df <- read.csv(
  metadata_file,
  check.names = FALSE,
  stringsAsFactors = FALSE
)

# ------------------------------------------------------------
# Identify columns
# ------------------------------------------------------------

find_column <- function(df, candidates) {
  normalized <- tolower(trimws(colnames(df)))

  for (candidate in candidates) {
    index <- match(tolower(candidate), normalized)

    if (!is.na(index)) {
      return(colnames(df)[index])
    }
  }

  return(NULL)
}

gene_column <- find_column(
  expression_df,
  c("gene", "gene_id", "gene_name", "geneid", "symbol")
)

sample_column <- find_column(
  metadata_df,
  c("sample_id", "sample", "sampleid")
)

group_column <- find_column(
  metadata_df,
  c("group", "condition", "class", "status")
)

if (is.null(gene_column)) {
  stop("Could not identify the gene identifier column.")
}

if (is.null(sample_column)) {
  stop("Metadata must contain a sample identifier column.")
}

if (is.null(group_column)) {
  stop("Metadata must contain a group/condition column.")
}

# ------------------------------------------------------------
# Prepare expression matrix
# ------------------------------------------------------------

rownames(expression_df) <- make.unique(
  as.character(expression_df[[gene_column]])
)

sample_columns <- setdiff(
  colnames(expression_df),
  gene_column
)

expression_matrix <- expression_df[, sample_columns, drop = FALSE]

expression_matrix[] <- lapply(
  expression_matrix,
  function(x) as.numeric(as.character(x))
)

expression_matrix <- as.matrix(expression_matrix)

storage.mode(expression_matrix) <- "numeric"

# Remove genes with missing values
keep_complete <- apply(
  expression_matrix,
  1,
  function(x) all(is.finite(x))
)

expression_matrix <- expression_matrix[keep_complete, , drop = FALSE]

# ------------------------------------------------------------
# Match metadata to expression samples
# ------------------------------------------------------------

metadata_df[[sample_column]] <- as.character(
  metadata_df[[sample_column]]
)

metadata_df[[group_column]] <- as.character(
  metadata_df[[group_column]]
)

common_samples <- intersect(
  colnames(expression_matrix),
  metadata_df[[sample_column]]
)

if (length(common_samples) < 2) {
  stop(
    "Fewer than two samples match between expression data and metadata."
  )
}

expression_matrix <- expression_matrix[, common_samples, drop = FALSE]

metadata_df <- metadata_df[
  match(common_samples, metadata_df[[sample_column]]),
  ,
  drop = FALSE
]

rownames(metadata_df) <- metadata_df[[sample_column]]

groups <- factor(metadata_df[[group_column]])

if (nlevels(groups) != 2) {
  stop(
    paste(
      "The first analysis version requires exactly two groups.",
      "Detected:",
      nlevels(groups)
    )
  )
}

# ------------------------------------------------------------
# Make sure reference group is first
# ------------------------------------------------------------

groups <- droplevels(groups)

group_names <- levels(groups)

message(
  "Groups: ",
  paste(group_names, collapse = " vs ")
)

message(
  "Samples: ",
  length(common_samples)
)

message(
  "Genes: ",
  nrow(expression_matrix)
)

# ------------------------------------------------------------
# Differential expression
# ------------------------------------------------------------

if (expression_type %in% c(
  "raw",
  "raw counts",
  "raw_count",
  "raw_counts",
  "count",
  "counts",
  "automatic"
)) {

  message("Running DESeq2...")

  # DESeq2 requires non-negative integer counts.
  if (any(expression_matrix < 0)) {
    stop("Raw count data cannot contain negative values.")
  }

  if (any(abs(expression_matrix - round(expression_matrix)) > 1e-8)) {
    stop(
      "Raw RNA-seq counts must be integer-like values. ",
      "If your data are normalized, choose the normalized/log-transformed option."
    )
  }

  count_matrix <- round(expression_matrix)

  dds <- DESeqDataSetFromMatrix(
    countData = count_matrix,
    colData = data.frame(
      group = groups,
      row.names = common_samples
    ),
    design = ~group
  )

  # Remove genes with no counts across all samples.
  dds <- dds[rowSums(counts(dds)) > 0, ]

  # DESeq2 can fail on extremely small or unusually uniform
  # datasets when the dispersion trend cannot be fitted.
  # In that specific case, use gene-wise dispersion estimates
  # and record that the fallback was required.

  deseq2_fallback <- FALSE

  dds <- tryCatch(
    {
      DESeq(dds)
    },
    error = function(e) {

      if (grepl(
        "all gene-wise dispersion estimates are within 2 orders of magnitude",
        conditionMessage(e),
        fixed = TRUE
      )) {

        message(
          "Standard DESeq2 dispersion fitting failed. ",
          "Using gene-wise dispersion fallback."
        )

        dds_fallback <- estimateSizeFactors(dds)

        dds_fallback <- estimateDispersionsGeneEst(
          dds_fallback
        )

        dispersions(dds_fallback) <-
          mcols(dds_fallback)$dispGeneEst

        dds_fallback <- nbinomWaldTest(
          dds_fallback
        )

        deseq2_fallback <<- TRUE

        return(dds_fallback)
      }

      stop(e)
    }
  )
  results_df <- as.data.frame(
    results(
      dds,
      contrast = c("group", group_names[2], group_names[1])
    )
  )

  results_df$gene <- rownames(results_df)

  results_df <- results_df[, c(
    "gene",
    "log2FoldChange",
    "pvalue",
    "padj"
  )]

} else if (expression_type %in% c(
  "normalized",
  "normalized expression",
  "log-transformed",
  "log transformed",
  "log_expression",
  "log"
)) {

  message("Running limma...")

  design <- model.matrix(~groups)

  fit <- lmFit(
    expression_matrix,
    design
  )

  fit <- eBayes(fit)

  results_df <- topTable(
    fit,
    coef = 2,
    number = Inf,
    sort.by = "P"
  )

  results_df$gene <- rownames(results_df)

  results_df <- results_df[, c(
    "gene",
    "logFC",
    "P.Value",
    "adj.P.Val"
  )]

  colnames(results_df) <- c(
    "gene",
    "log2FoldChange",
    "pvalue",
    "padj"
  )

} else {

  stop(
    paste(
      "Unsupported expression type:",
      expression_type
    )
  )
}

# ------------------------------------------------------------
# Standardize output
# ------------------------------------------------------------

results_df$log2FoldChange <- as.numeric(
  results_df$log2FoldChange
)

results_df$pvalue <- as.numeric(
  results_df$pvalue
)

results_df$padj <- as.numeric(
  results_df$padj
)

results_df$direction <- ifelse(
  is.na(results_df$log2FoldChange),
  "Unknown",
  ifelse(
    results_df$log2FoldChange > 0,
    paste0(group_names[2], " up"),
    ifelse(
      results_df$log2FoldChange < 0,
      paste0(group_names[1], " up"),
      "No change"
    )
  )
)

results_df <- results_df[
  order(
    results_df$padj,
    results_df$pvalue,
    na.last = TRUE
  ),
]

# ------------------------------------------------------------
# Save standardized results
# ------------------------------------------------------------

write.csv(
  results_df,
  output_file,
  row.names = FALSE
)
# ------------------------------------------------------------
# Save analysis status
# ------------------------------------------------------------

status_file <- paste0(
  tools::file_path_sans_ext(output_file),
  "_status.txt"
)

method_name <- if (
  expression_type == "raw counts"
) {
  "DESeq2"
} else {
  "limma"
}

dispersion_status <- if (
  expression_type == "raw counts" &&
  deseq2_fallback
) {
  "Gene-wise fallback"
} else if (
  expression_type == "raw counts"
) {
  "Standard DESeq2 dispersion fitting"
} else {
  "Not applicable"
}

writeLines(
  c(
    "Analysis status: Completed",
    paste0("Method: ", method_name),
    paste0("Dispersion estimation: ", dispersion_status)
  ),
  status_file
)

message(
  "Status written to: ",
  status_file
)

message(
  "Analysis completed successfully."
)

message(
  "Results written to: ",
  output_file
)
