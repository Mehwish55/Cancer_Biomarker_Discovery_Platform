library(readr)
library(dplyr)

base <- '/mnt/d/Cancer_Biomarker_Project'

deg <- read_csv(file.path(base, 'results/validation/LUAD_Top40_DESeq2_validation.csv'), show_col_types=FALSE)
roc <- read_csv(file.path(base, 'results/validation/LUAD_Top40_ROC_AUC_results.csv'), show_col_types=FALSE)
rank <- read_csv(file.path(base, 'results/validation/LUAD_Top40_final_validation_ranking.csv'), show_col_types=FALSE)
stab <- read_csv(file.path(base, 'results/validation/ml/biomarker_stability.csv'), show_col_types=FALSE)
rf <- read_csv(file.path(base, 'results/validation/ml/RandomForest_feature_importance.csv'), show_col_types=FALSE)

final <- rank %>%
  left_join(
    roc %>% select(gene_name, AUC, CI_lower, CI_upper, sensitivity, specificity, ROC_rank),
    by='gene_name'
  ) %>%
  left_join(
    stab %>% select(gene_name, stability_score, stability_rank, top10_stability, top20_stability),
    by='gene_name'
  ) %>%
  left_join(
    rf %>% select(gene_name, importance, ML_rank),
    by='gene_name'
  ) %>%
  left_join(
    deg %>% select(gene_name, baseMean, lfcSE, stat),
    by='gene_name'
  ) %>%
  arrange(validation_rank)

dir.create(file.path(base, 'results/final'), recursive=TRUE, showWarnings=FALSE)

write_csv(
  final,
  file.path(base, 'results/final/LUAD_final_40_biomarker_evidence_table.csv')
)

write_csv(
  final %>% slice_head(n=15),
  file.path(base, 'results/final/LUAD_final_top15_biomarkers.csv')
)

cat('\n============================================\n')
cat('FINAL BIOMARKER TABLE CREATED\n')
cat('============================================\n')
cat('Genes:', nrow(final), '\n')
cat('Top 15 saved.\n')
cat('Output:', file.path(base, 'results/final/LUAD_final_40_biomarker_evidence_table.csv'), '\n')
