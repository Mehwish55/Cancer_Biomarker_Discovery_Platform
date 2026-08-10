import pandas as pd

f = '/mnt/d/Cancer_Biomarker_Project/results/validation/LUAD_Top40_validation_expression.csv'

x = pd.read_csv(f)

print('Shape:', x.shape)
print('Samples:', x['sample_id'].nunique())
print('Genes:', x['gene_id'].nunique())
print()
print(x.head())
print()

counts = x.groupby('sample_id')['gene_id'].nunique()

print('Minimum genes/sample:', counts.min())
print('Maximum genes/sample:', counts.max())
print('Samples with <40 genes:', (counts < 40).sum())
