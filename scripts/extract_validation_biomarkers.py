import os
import glob
import pandas as pd

PROJECT = '/mnt/d/Cancer_Biomarker_Project'

BIOMARKERS = os.path.join(
    PROJECT,
    'results',
    'Top40_LUAD_biomarker_candidates.csv'
)

INPUT_DIR = os.path.join(
    PROJECT,
    'data',
    'validation',
    'TCGA-LUAD'
)

OUTPUT = os.path.join(
    PROJECT,
    'results',
    'validation',
    'LUAD_Top40_validation_expression.csv'
)

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# Load the 40 candidate genes
genes = pd.read_csv(BIOMARKERS)

target_genes = set(
    genes['gene_id']
    .astype(str)
    .str.replace(r'\..*$', '', regex=True)
)

print('Target biomarkers:', len(target_genes))

files = sorted(
    glob.glob(
        os.path.join(
            INPUT_DIR,
            '**',
            '*.tsv'
        ),
        recursive=True
    )
)

print('Validation files:', len(files))

results = []

for i, filepath in enumerate(files, 1):

    try:
        df = pd.read_csv(
            filepath,
            sep='\t',
            comment='#',
            usecols=['gene_id', 'gene_name', 'unstranded']
        )

        df['gene_id_clean'] = (
            df['gene_id']
            .astype(str)
            .str.replace(r'\..*$', '', regex=True)
        )

        selected = df[
            df['gene_id_clean'].isin(target_genes)
        ][
            ['gene_id_clean', 'gene_name', 'unstranded']
        ].copy()

        sample_id = os.path.basename(filepath).replace(
            '.rna_seq.augmented_star_gene_counts.tsv',
            ''
        )

        selected['sample_id'] = sample_id

        results.append(selected)

        if i % 50 == 0:
            print(f'Processed {i}/{len(files)} files')

    except Exception as e:
        print('ERROR:', filepath)
        print(e)

if not results:
    raise RuntimeError('No biomarker genes were extracted.')

combined = pd.concat(results, ignore_index=True)

combined = combined.rename(
    columns={
        'gene_id_clean': 'gene_id',
        'unstranded': 'count'
    }
)

combined = combined[
    ['sample_id', 'gene_id', 'gene_name', 'count']
]

combined.to_csv(
    OUTPUT,
    index=False
)

print()
print('Finished!')
print('Rows:', len(combined))
print('Samples:', combined['sample_id'].nunique())
print('Genes:', combined['gene_id'].nunique())
print('Output:', OUTPUT)
