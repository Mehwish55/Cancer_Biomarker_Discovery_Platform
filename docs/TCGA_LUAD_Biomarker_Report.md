# AI-Assisted Cancer Biomarker Discovery Using TCGA-LUAD RNA-seq Data

## 1. Project Overview

This project aims to identify potential molecular biomarkers associated with Lung Adenocarcinoma (LUAD) using transcriptomic RNA-seq data from The Cancer Genome Atlas (TCGA).

The workflow combines differential gene expression analysis, functional enrichment analysis, pathway investigation, and visualization to discover genes and biological processes involved in cancer progression.

---

## 2. Dataset

**Dataset:** TCGA Lung Adenocarcinoma (TCGA-LUAD)

**Data Type:** RNA-seq gene expression data

**Analysis Platform:** R / Bioconductor

**Main Packages Used:**

- DESeq2
- clusterProfiler
- org.Hs.eg.db
- enrichplot
- data.table
- ggplot2

---

## 3. Bioinformatics Workflow

RNA-seq Expression Data

↓

Quality Processing and Data Preparation

↓

Differential Gene Expression Analysis

↓

Identification of Significant Genes

↓

Gene Annotation (Ensembl ID to Gene Symbol)

↓

GO Functional Enrichment Analysis

↓

KEGG Pathway Analysis

↓

Biological Interpretation of Candidate Biomarkers

---

## 4. Differential Expression Analysis

Differential expression analysis was performed to identify genes significantly altered in LUAD samples.

Significance criteria:

- Adjusted p-value (padj) < 0.05
- Biological relevance based on log2 fold change

The analysis identified significant upregulated and downregulated genes.

---

## 5. Top Candidate Biomarkers

### Upregulated Genes

| Gene | Possible Role |
|---|---|
| FAM83A | Associated with cancer progression and tumor growth |
| PYCR1 | Involved in metabolic adaptation |
| AFAP1-AS1 | Cancer-associated long non-coding RNA |
| TOP2A | Marker of cell proliferation |
| B3GNT3 | Associated with tumor-related processes |


### Downregulated Genes

| Gene | Possible Role |
|---|---|
| PECAM1 | Endothelial and vascular signaling |
| S1PR1 | Immune regulation |
| EPAS1 | Hypoxia-related signaling |
| RGCC | Cell cycle regulation |

---

## 6. Functional Enrichment Analysis

GO enrichment analysis revealed significant biological processes including:

- Extracellular matrix organization
- Cell-cell adhesion
- Immune-related processes
- Signal transduction pathways

These pathways are important in:

- Tumor invasion
- Metastasis
- Tumor microenvironment interaction

---

## 7. KEGG Pathway Analysis

KEGG analysis identified significant pathways including:

- Neuroactive ligand-receptor interaction
- Immune-related pathways
- Hormone signaling pathways
- Disease-associated pathways

These results indicate alterations in cellular communication and cancer-associated signaling networks.

---

## 8. Results Generated

The project produced:

- Differentially expressed gene table
- Volcano plot
- GO enrichment plots
- KEGG pathway plots
- Candidate biomarker list

---

## 9. Future Development

Future improvements include:

- Machine learning-based biomarker prediction
- Random Forest and XGBoost classification models
- Survival analysis using patient clinical data
- Integration with drug discovery pipelines

---

## 10. Technologies

Programming:
- R
- Python

Bioinformatics
- Bioconductor
- DESeq2
- clusterProfiler

Data Science:
- Machine Learning
- Statistical Analysis
- Data Visualization

---

# 11. Visualization of Results

## Differential Expression Analysis

The volcano plot shows significantly differentially expressed genes between LUAD samples and controls.

![Volcano Plot](../figures/Volcano_plot_TCGA_LUAD.png)


## Gene Ontology Enrichment Analysis

GO enrichment analysis identified important biological processes associated with cancer development.

![GO Enrichment](../figures/GO_enrichment_TCGA_LUAD.png)


## KEGG Pathway Analysis

KEGG analysis revealed important signaling pathways involved in LUAD biology.

![KEGG Pathways](../figures/KEGG_pathway_TCGA_LUAD.png)

---

## Conclusion

This project demonstrates a reproducible computational biology workflow for discovering potential LUAD biomarkers from RNA-seq data and provides a foundation for AI-driven cancer research applications.
