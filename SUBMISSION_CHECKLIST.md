# Springer Spine Deformity submission checklist

**Repo:** github.com/sayujks0071/scoliosis (tag `v1.1-clinical-reframe`, commit `b448198`)
**Local manuscript source:** `~/life/manuscript/`
**Overleaf bundle:** `~/life/manuscript_overleaf_v1.1.zip` (5.5 MB, generated 2026-05-11)
**Editorial Manager:** https://www.editorialmanager.com/SPDE/

## Step 1 — Compile to PDF (Overleaf, 5 min)

1. Sign into https://www.overleaf.com
2. New Project → Upload Project → select `~/life/manuscript_overleaf_v1.1.zip`
3. Set main document to `main.tex`
4. Click "Recompile"
5. Verify clean compilation:
   - PDF title reads: "Active Geometric Maintenance of the Spinal S-Curve Against Gravity..."
   - Abstract is 4 paragraphs (Background / Methods / Results / Conclusions) with bold labels
   - Figure 2b appears with caption "Mechanosensor proteins are interior-rigid"
   - No "Spacetime", "Lagrangian of the Growing Spine", "Vector-Scalar Mismatch", or "Thermodynamic Standing Wave" anywhere in body
   - Cobb-angle correlation R²=0.775 in body matches abstract
   - No "?" placeholders for refs (would mean broken `\ref{}`)
6. Download as `submission_manuscript_v1.1.pdf`
7. Compile `cover_letter_spine_deformity.tex` separately → `cover_letter.pdf`

## Step 2 — Springer submission package (30 min)

Editorial Manager will ask for:

### Required uploads
- **Manuscript PDF:** `submission_manuscript_v1.1.pdf` (from Overleaf)
- **Manuscript LaTeX source:** zip up `manuscript/main.tex`, `sections/*.tex`, `references.bib`, `figures/`
- **Cover letter:** `cover_letter.pdf`
- **Highlights:** copy bullets from `~/life/manuscript/highlights_spine_deformity.txt` into the form field (5 bullets, ≤85 chars each)

### Required metadata
- **Article type:** Original Article
- **Title:** Active Geometric Maintenance of the Spinal S-Curve Against Gravity: An Information–Mechanical Coupling Model for Adolescent Idiopathic Scoliosis Onset
- **Short title (≤70 char):** Active Geometric Spinal Maintenance and AIS Onset
- **Keywords:** adolescent idiopathic scoliosis; gravitational loading; postural control; AlphaFold; mechanosensors; biomechanics; Cosserat rod; allometric scaling
- **Author:** Dr. Sayuj Krishnan S, MBBS, DNB (Neurosurgery), Yashoda Hospitals Hyderabad, dr.sayujkrishnan@gmail.com, ORCID 0009-0009-5523-9979
- **Funding:** None (personal project)
- **Competing interests:** None
- **Data availability:** github.com/sayujks0071/scoliosis (release tag v1.0-submission for reproduction; v1.1-clinical-reframe for current submission state). Zenodo DOI to mint after acceptance.
- **Code availability:** included in repo above

### Suggested reviewers (5 — copy from cover letter)
- Prof. Stuart L. Weinstein (Univ. of Iowa) — AIS natural history, bracing trials
- Prof. Alain Moreau (Univ. Montréal) — AIS molecular biology, melatonin/POC5
- Prof. Carl-Eric Aubin (Polytechnique Montréal) — spine biomechanics, Cosserat rod
- Prof. Peter O. Newton (Rady Children's, San Diego) — pediatric spine, Lenke
- Prof. Tomohiko Kayano (Saitama Medical University) — LBX1 / AIS genetics

## Step 3 — Pre-submission self-checks

- [ ] Word count abstract ≤ 350 (current: 177 prose words ✓)
- [ ] All numbers in abstract appear identically in results body (verified by sub-agent in iteration 11)
- [ ] No physics-as-worldview language in title, abstract, or any inputted body section (audited iteration 11; only orphan files biophysical_origins.tex / theory.tex / methods.tex retain such terms but those don't compile into the PDF)
- [ ] Figure 2b (`fig_hinge_density.pdf`) renders and is referenced in text (results.tex:25)
- [ ] All 232 BibTeX entries validated (passed iteration 0)
- [ ] Cover letter hits 3 falsifiable predictions (proprioceptive biomarker, NAD+ rescue, brace-timing)
- [ ] Highlights are clinical-language 5-bullet form

## Step 4 — Submit

- Editorial Manager → Submit → confirm. Initial editorial decision typically 2–4 weeks.

## After submission

- Mint Zenodo DOI from GitHub release `v1.1-clinical-reframe` (Zenodo settings → enable repo → publish a release; DOI will be assigned)
- Update `references.bib` and `cover_letter.tex` with the Zenodo DOI
- Cron jobs continue running (`correlation_refresh.sh` 03:00 IST, `pubmed_spine_watch.sh` 06:00 IST) — they'll surface drift in the AFCC pipeline or new related publications

## Files referenced

- Local: `~/life/manuscript/`, `~/life/manuscript_overleaf_v1.1.zip`
- Strategy: `~/jupyterlab/scoliosis_publication_strategy/`
- Drafts: `~/jupyterlab/scoliosis_publication_strategy/manuscript_drafts/`
- Results: `~/jupyterlab/scoliosis_publication_strategy/results/`
- Cron: `~/jupyterlab/scoliosis_publication_strategy/scripts/correlation_refresh.sh`, `pubmed_spine_watch.sh`
