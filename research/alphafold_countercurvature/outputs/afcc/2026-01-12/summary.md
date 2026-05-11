# Bolt-BioFold ⚡ Analysis Report

Sources: Mechanotransduction,Proprioception, Somite,Muscle,Proprioception, Cilia,Mechanotransduction, Mechanotransduction,Growth_Plate,Ion_Channel, Mechanotransduction,Nucleus,Cytoskeleton, Mechanotransduction,Hippo,Growth_Plate, Cilia,Centriole, Mechanotransduction,Adhesion, Cytoskeleton,Segmentation

## 1. Results Table
| Identity | Species | Length | pLDDT_mean | pLDDT_frac_low | PAE_mean | PAE_blockiness | Disorder_Proxy | Hinge_Cands | Rg | End_to_End | Curvature | Torsion | Anisotropy | Principal_Axis | Hotspots | Exposed_Frac | Charged_Patch | Domains | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PIEZO2 (Q9H5I5) | Homo sapiens | 709 | 79.4 | 0.21 | 17.0 | 2.8 | 0.14 | 0 | 43.4 | 28.4 | 0.329 | 1.428 | 4.44 | [-0.687, -0.068, 0.724] | 460:0.38; 239:0.38; 138:0.38 | 0.56 | 0.25 | 7 | MultiDomUncert |
| LBX1 (P52954) | Homo sapiens | 281 | 66.9 | 0.61 | 25.1 | 7.35 | 0.26 | 0 | 22.7 | 51.9 | 0.343 | 1.173 | 2.27 | [-0.222, -0.149, 0.964] | 83:0.39; 37:0.39; 34:0.38 | 0.93 | 0.36 | 3 | LowConf, MultiDomUncert |
| IFT88 (Q13099) | Homo sapiens | 824 | 76.3 | 0.29 | 19.4 | 2.43 | 0.23 | 1 | 38.3 | 92.4 | 0.358 | 1.121 | 2.8 | [-0.626, -0.157, 0.764] | 315:0.38; 643:0.38; 426:0.38 | 0.51 | 0.44 | 3 | MultiDomUncert |
| PIEZO1 (Q92508) | Homo sapiens | 2521 | 72.0 | 0.33 | 22.7 | 5.74 | 0.17 | 3 | 58.9 | 30.0 | 0.341 | 1.182 | 3.9 | [-0.270, -0.320, 0.908] | 458:0.44; 625:0.42; 513:0.41 | 0.46 | 0.27 | 35 | MultiDomUncert |
| LMNA (P02545) | Homo sapiens | 664 | 76.4 | 0.31 | 24.9 | 2.56 | 0.26 | 0 | 71.2 | 278.1 | 0.344 | 1.194 | 4.75 | [-0.668, -0.244, 0.703] | 508:0.40; 519:0.39; 30:0.38 | 0.87 | 0.4 | 3 | MultiDomUncert |
| YAP1 (P46937) | Homo sapiens | 504 | 57.4 | 0.74 | 27.5 | 9.26 | 0.45 | 2 | 23.6 | 11.4 | 0.321 | 1.628 | 1.99 | [-0.676, 0.732, 0.082] | 182:0.38; 241:0.38; 257:0.38 | 0.93 | 0.3 | 5 | LowConf, MultiDomUncert |
| POC5 (Q8NA72) | Homo sapiens | 575 | 64.0 | 0.61 | 25.6 | 3.51 | 0.49 | 5 | 87.3 | 307.4 | 0.364 | 0.848 | 24.69 | [-0.657, -0.161, 0.737] | 156:0.38; 247:0.38; 192:0.37 | 1.0 | 0.36 | 2 | LowConf, MultiDomUncert |
| ITGB1 (P05556) | Homo sapiens | 798 | 85.9 | 0.11 | 18.2 | 4.9 | 0.03 | 10 | 45.8 | 94.9 | 0.305 | 1.725 | 3.23 | [-0.504, -0.483, 0.716] | 193:0.39; 474:0.38; 521:0.38 | 0.34 | 0.35 | 10 | MultiDomUncert |
| FLNB (O75369) | Homo sapiens | 2602 | 76.3 | 0.24 | 27.0 | 8.93 | 0.04 | 158 | 55.9 | 35.9 | 0.277 | 2.133 | 2.25 | [0.559, 0.744, -0.367] | 1505:0.44; 2595:0.43; 1409:0.42 | 0.28 | 0.41 | 65 | MultiDomUncert |

### CSV Block
```csv
Identity,Species,Length,pLDDT_mean,pLDDT_frac_low,PAE_mean,PAE_blockiness,Disorder_Proxy,Hinge_Cands,Rg,End_to_End,Curvature,Torsion,Anisotropy,Principal_Axis,Hotspots,Exposed_Frac,Charged_Patch,Domains,Flags
PIEZO2 (Q9H5I5),Homo sapiens,709,79.4,0.21,17.0,2.8,0.14,0,43.4,28.4,0.329,1.428,4.44,"[-0.687, -0.068, 0.724]",460:0.38; 239:0.38; 138:0.38,0.56,0.25,7,MultiDomUncert
LBX1 (P52954),Homo sapiens,281,66.9,0.61,25.1,7.35,0.26,0,22.7,51.9,0.343,1.173,2.27,"[-0.222, -0.149, 0.964]",83:0.39; 37:0.39; 34:0.38,0.93,0.36,3,"LowConf, MultiDomUncert"
IFT88 (Q13099),Homo sapiens,824,76.3,0.29,19.4,2.43,0.23,1,38.3,92.4,0.358,1.121,2.8,"[-0.626, -0.157, 0.764]",315:0.38; 643:0.38; 426:0.38,0.51,0.44,3,MultiDomUncert
PIEZO1 (Q92508),Homo sapiens,2521,72.0,0.33,22.7,5.74,0.17,3,58.9,30.0,0.341,1.182,3.9,"[-0.270, -0.320, 0.908]",458:0.44; 625:0.42; 513:0.41,0.46,0.27,35,MultiDomUncert
LMNA (P02545),Homo sapiens,664,76.4,0.31,24.9,2.56,0.26,0,71.2,278.1,0.344,1.194,4.75,"[-0.668, -0.244, 0.703]",508:0.40; 519:0.39; 30:0.38,0.87,0.4,3,MultiDomUncert
YAP1 (P46937),Homo sapiens,504,57.4,0.74,27.5,9.26,0.45,2,23.6,11.4,0.321,1.628,1.99,"[-0.676, 0.732, 0.082]",182:0.38; 241:0.38; 257:0.38,0.93,0.3,5,"LowConf, MultiDomUncert"
POC5 (Q8NA72),Homo sapiens,575,64.0,0.61,25.6,3.51,0.49,5,87.3,307.4,0.364,0.848,24.69,"[-0.657, -0.161, 0.737]",156:0.38; 247:0.38; 192:0.37,1.0,0.36,2,"LowConf, MultiDomUncert"
ITGB1 (P05556),Homo sapiens,798,85.9,0.11,18.2,4.9,0.03,10,45.8,94.9,0.305,1.725,3.23,"[-0.504, -0.483, 0.716]",193:0.39; 474:0.38; 521:0.38,0.34,0.35,10,MultiDomUncert
FLNB (O75369),Homo sapiens,2602,76.3,0.24,27.0,8.93,0.04,158,55.9,35.9,0.277,2.133,2.25,"[0.559, 0.744, -0.367]",1505:0.44; 2595:0.43; 1409:0.42,0.28,0.41,65,MultiDomUncert
```

## 2. Key Plots Summary
- `POC5_plddt.png`: pLDDT profile for POC5
- `POC5_pae.png`: PAE heatmap for POC5
- `FLNB_plddt.png`: pLDDT profile for FLNB
- `FLNB_pae.png`: PAE heatmap for FLNB
- `LMNA_plddt.png`: pLDDT profile for LMNA
- `LMNA_pae.png`: PAE heatmap for LMNA

## 3. Interpretation
**Family: Cilia,Centriole**
- **POC5**: POC5: Anisotropy=24.7, pLDDT=64. Highly extended/fibrous. Warning: Low confidence structure. Detected 5 potential flexible hinges; may act as mechanical sensor/switch. (Conf: Low). Test: Verify fiber formation in vivo; test mechanical stiffness.

**Family: Cilia,Mechanotransduction**
- **IFT88**: IFT88: Anisotropy=2.8, pLDDT=76. Intermediate shape.  Detected 1 potential flexible hinges; may act as mechanical sensor/switch. (Conf: Medium). Test: Mutate hinge region to test effect on mechanosensitivity.

**Family: Cytoskeleton,Segmentation**
- **FLNB**: FLNB: Anisotropy=2.2, pLDDT=76. Intermediate shape.  Detected 158 potential flexible hinges; may act as mechanical sensor/switch. (Conf: Medium). Test: Mutate hinge region to test effect on mechanosensitivity.

**Family: Mechanotransduction,Adhesion**
- **ITGB1**: ITGB1: Anisotropy=3.2, pLDDT=86. Highly extended/fibrous.  Rigid rod-like geometry suggests load-bearing capacity or long-range connectivity. (Conf: High). Test: Mutate hinge region to test effect on mechanosensitivity.

**Family: Mechanotransduction,Growth_Plate,Ion_Channel**
- **PIEZO1**: PIEZO1: Anisotropy=3.9, pLDDT=72. Highly extended/fibrous.  Rigid rod-like geometry suggests load-bearing capacity or long-range connectivity. (Conf: Medium). Test: Mutate hinge region to test effect on mechanosensitivity.

**Family: Mechanotransduction,Hippo,Growth_Plate**
- **YAP1**: YAP1: Anisotropy=2.0, pLDDT=57. Intermediate shape. Warning: Low confidence structure. Detected 2 potential flexible hinges; may act as mechanical sensor/switch. (Conf: Low). Test: Mutate hinge region to test effect on mechanosensitivity.

**Family: Mechanotransduction,Nucleus,Cytoskeleton**
- **LMNA**: LMNA: Anisotropy=4.8, pLDDT=76. Highly extended/fibrous.  Rigid rod-like geometry suggests load-bearing capacity or long-range connectivity. (Conf: Medium). Test: Verify fiber formation in vivo; test mechanical stiffness.

**Family: Mechanotransduction,Proprioception**
- **PIEZO2**: PIEZO2: Anisotropy=4.4, pLDDT=79. Highly extended/fibrous.  Rigid rod-like geometry suggests load-bearing capacity or long-range connectivity. (Conf: Medium). Test: Verify fiber formation in vivo; test mechanical stiffness.

**Family: Somite,Muscle,Proprioception**
- **LBX1**: LBX1: Anisotropy=2.3, pLDDT=67. Intermediate shape. Warning: Low confidence structure. Standard globular domain, likely biochemical role or node in network. (Conf: Low). Test: Check expression timing relative to spine straightening.


## 4. Best Next Move
Cluster by geometry and correlate curvature metrics with known phenotype genes.

## 5. Quality & Reproducibility Checklist
- Data Source: AlphaFold DB (fetched via scripts/02_fetch_afdb.py)
- Date/Time: 2026-01-12 22:02:01
- Code Version: 034980e
- Parameters: pLDDT threshold >= 70 for geometry; Smoothing window = default
- Notes: 9 structures analyzed. Source config: research/alphafold_countercurvature/config/targets.yaml
