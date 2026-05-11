# Bolt-BioFold ⚡ Analysis Report

Sources: Mechanotransduction, Somite, Cilia, Signaling, Nucleus, Cytoskeleton

## 1. Results Table
| Identity | Species | Length | pLDDT_mean | pLDDT_frac_low | PAE_mean | PAE_blockiness | Disorder_Proxy | Hinge_Cands | Rg | End_to_End | Curvature | Torsion | Anisotropy | Principal_Axis | Hotspots | Exposed_Frac | Charged_Patch | Domains | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PIEZO2 (Q9H5I5) | Homo sapiens | 709 | 79.4 | 0.21 | 17.0 | 2.8 | 0.14 | 0 | 43.4 | 28.4 | 0.329 | 1.428 | 4.44 | [-0.687, -0.068, 0.724] | 460:0.38; 239:0.38; 138:0.38 | 0.56 | 0.25 | 7 | MultiDomUncert |
| LBX1 (P52954) | Homo sapiens | 281 | 66.9 | 0.61 | 25.1 | 7.35 | 0.26 | 0 | 22.7 | 51.9 | 0.343 | 1.173 | 2.27 | [-0.222, -0.149, 0.964] | 83:0.39; 37:0.39; 34:0.38 | 0.93 | 0.36 | 3 | LowConf, MultiDomUncert |
| IFT88 (Q13099) | Homo sapiens | 824 | 76.3 | 0.29 | 19.4 | 2.43 | 0.23 | 1 | 38.3 | 92.4 | 0.358 | 1.121 | 2.8 | [-0.626, -0.157, 0.764] | 315:0.38; 643:0.38; 426:0.38 | 0.51 | 0.44 | 3 | MultiDomUncert |
| PIEZO1 (Q92508) | Homo sapiens | 2521 | 72.0 | 0.33 | 22.7 | 5.74 | 0.17 | 3 | 58.9 | 30.0 | 0.341 | 1.182 | 3.9 | [-0.270, -0.320, 0.908] | 458:0.44; 625:0.42; 513:0.41 | 0.46 | 0.27 | 35 | MultiDomUncert |
| LMNA (P02545) | Homo sapiens | 664 | 76.4 | 0.31 | 24.9 | 2.56 | 0.26 | 0 | 71.2 | 278.1 | 0.344 | 1.194 | 4.75 | [-0.668, -0.244, 0.703] | 508:0.40; 519:0.39; 30:0.38 | 0.87 | 0.4 | 3 | MultiDomUncert |
| NF1 (P21359) | Homo sapiens | 593 | 87.2 | 0.11 | 9.5 | 2.42 | 0.07 | 1 | 26.1 | 40.7 | 0.35 | 1.116 | 1.93 | [-0.387, -0.133, 0.912] | 221:0.38; 178:0.38; 274:0.38 | 0.34 | 0.37 | 6 | OK |
| EMD (P50402) | Homo sapiens | 254 | 60.3 | 0.72 | 26.5 | 9.13 | 0.48 | 1 | 21.0 | 19.8 | 0.35 | 1.112 | 4.29 | [-0.478, -0.124, 0.870] | 8:0.38; 11:0.38; 34:0.38 | 0.94 | 0.23 | 2 | LowConf, MultiDomUncert |
| FLNA (P21333) | Homo sapiens | 2647 | 76.5 | 0.23 | 26.8 | 9.88 | 0.05 | 116 | 56.9 | 27.0 | 0.28 | 2.131 | 2.5 | [0.486, 0.735, -0.473] | 1533:0.44; 1946:0.43; 2640:0.43 | 0.28 | 0.38 | 73 | MultiDomUncert |

### CSV Block
```csv
Identity,Species,Length,pLDDT_mean,pLDDT_frac_low,PAE_mean,PAE_blockiness,Disorder_Proxy,Hinge_Cands,Rg,End_to_End,Curvature,Torsion,Anisotropy,Principal_Axis,Hotspots,Exposed_Frac,Charged_Patch,Domains,Flags
PIEZO2 (Q9H5I5),Homo sapiens,709,79.4,0.21,17.0,2.8,0.14,0,43.4,28.4,0.329,1.428,4.44,"[-0.687, -0.068, 0.724]",460:0.38; 239:0.38; 138:0.38,0.56,0.25,7,MultiDomUncert
LBX1 (P52954),Homo sapiens,281,66.9,0.61,25.1,7.35,0.26,0,22.7,51.9,0.343,1.173,2.27,"[-0.222, -0.149, 0.964]",83:0.39; 37:0.39; 34:0.38,0.93,0.36,3,"LowConf, MultiDomUncert"
IFT88 (Q13099),Homo sapiens,824,76.3,0.29,19.4,2.43,0.23,1,38.3,92.4,0.358,1.121,2.8,"[-0.626, -0.157, 0.764]",315:0.38; 643:0.38; 426:0.38,0.51,0.44,3,MultiDomUncert
PIEZO1 (Q92508),Homo sapiens,2521,72.0,0.33,22.7,5.74,0.17,3,58.9,30.0,0.341,1.182,3.9,"[-0.270, -0.320, 0.908]",458:0.44; 625:0.42; 513:0.41,0.46,0.27,35,MultiDomUncert
LMNA (P02545),Homo sapiens,664,76.4,0.31,24.9,2.56,0.26,0,71.2,278.1,0.344,1.194,4.75,"[-0.668, -0.244, 0.703]",508:0.40; 519:0.39; 30:0.38,0.87,0.4,3,MultiDomUncert
NF1 (P21359),Homo sapiens,593,87.2,0.11,9.5,2.42,0.07,1,26.1,40.7,0.35,1.116,1.93,"[-0.387, -0.133, 0.912]",221:0.38; 178:0.38; 274:0.38,0.34,0.37,6,OK
EMD (P50402),Homo sapiens,254,60.3,0.72,26.5,9.13,0.48,1,21.0,19.8,0.35,1.112,4.29,"[-0.478, -0.124, 0.870]",8:0.38; 11:0.38; 34:0.38,0.94,0.23,2,"LowConf, MultiDomUncert"
FLNA (P21333),Homo sapiens,2647,76.5,0.23,26.8,9.88,0.05,116,56.9,27.0,0.28,2.131,2.5,"[0.486, 0.735, -0.473]",1533:0.44; 1946:0.43; 2640:0.43,0.28,0.38,73,MultiDomUncert
```

## 2. Key Plots Summary
- `PIEZO2_plddt.png`: pLDDT profile for PIEZO2
- `PIEZO2_pae.png`: PAE heatmap for PIEZO2
- `FLNA_plddt.png`: pLDDT profile for FLNA
- `FLNA_pae.png`: PAE heatmap for FLNA
- `LMNA_plddt.png`: pLDDT profile for LMNA
- `LMNA_pae.png`: PAE heatmap for LMNA

## 3. Interpretation
**Family: Cilia**
- **IFT88**: IFT88: Anisotropy=2.8, pLDDT=76. Intermediate shape.  Detected 1 potential flexible hinges; may act as mechanical sensor/switch. (Conf: Medium). Test: Mutate hinge region to test effect on mechanosensitivity.

**Family: Cytoskeleton**
- **FLNA**: FLNA: Anisotropy=2.5, pLDDT=77. Intermediate shape.  Detected 116 potential flexible hinges; may act as mechanical sensor/switch. (Conf: Medium). Test: Mutate hinge region to test effect on mechanosensitivity.

**Family: Mechanotransduction**
- **PIEZO2**: PIEZO2: Anisotropy=4.4, pLDDT=79. Highly extended/fibrous.  Rigid rod-like geometry suggests load-bearing capacity or long-range connectivity. (Conf: Medium). Test: Verify fiber formation in vivo; test mechanical stiffness.
- **PIEZO1**: PIEZO1: Anisotropy=3.9, pLDDT=72. Highly extended/fibrous.  Rigid rod-like geometry suggests load-bearing capacity or long-range connectivity. (Conf: Medium). Test: Mutate hinge region to test effect on mechanosensitivity.
- **LMNA**: LMNA: Anisotropy=4.8, pLDDT=76. Highly extended/fibrous.  Rigid rod-like geometry suggests load-bearing capacity or long-range connectivity. (Conf: Medium). Test: Verify fiber formation in vivo; test mechanical stiffness.

**Family: Nucleus**
- **EMD**: EMD: Anisotropy=4.3, pLDDT=60. Highly extended/fibrous. Warning: Low confidence structure. Detected 1 potential flexible hinges; may act as mechanical sensor/switch. (Conf: Low). Test: Verify fiber formation in vivo; test mechanical stiffness.

**Family: Signaling**
- **NF1**: NF1: Anisotropy=1.9, pLDDT=87. Intermediate shape.  Detected 1 potential flexible hinges; may act as mechanical sensor/switch. (Conf: High). Test: Mutate hinge region to test effect on mechanosensitivity.

**Family: Somite**
- **LBX1**: LBX1: Anisotropy=2.3, pLDDT=67. Intermediate shape. Warning: Low confidence structure. Standard globular domain, likely biochemical role or node in network. (Conf: Low). Test: Check expression timing relative to spine straightening.


## 4. Best Next Move
Cluster by geometry and correlate curvature metrics with known phenotype genes.

## 5. Quality & Reproducibility Checklist
- Data Source: AlphaFold DB (fetched via scripts/02_fetch_afdb.py)
- Date/Time: 2026-01-23 21:37:08
- Code Version: d2377ce
- Parameters: pLDDT threshold >= 70 for geometry; Smoothing window = default
- Notes: 8 structures analyzed. Source config: research/alphafold_countercurvature/config/targets.yaml
