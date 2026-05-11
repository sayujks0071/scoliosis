# Agent Skills Usage Examples

Concrete examples demonstrating how to use the installed agent skills for research workflows.

## Table of Contents

1. [Research Workflow Skill](#research-workflow-skill)
2. [Document Skills (docx, pdf, pptx, xlsx)](#document-skills)
3. [Doc Co-Authoring Skill](#doc-co-authoring)
4. [Workflow Integration](#workflow-integration)

---

## Research Workflow Skill

### Example 1: Create New Theoretical Framework

**User request:**

```
Help me create a new theoretical framework document about protein mechanics using the Cosserat rod model
```

**What happens:**

1. Research-workflow skill activates
2. Provides theoretical-framework template
3. Guides through structured document creation
4. Offers domain knowledge reference for Cosserat theory

**Result:**

- Structured framework document with proper sections
- Mathematical notation following conventions
- References to domain concepts

---

### Example 2: Convert Research Markdown to LaTeX

**User request:**

```
Convert the scoliosis theoretical framework to LaTeX for manuscript submission
```

**What happens:**

1. Research-workflow skill activates
2. Runs `md_to_latex.py` script
3. Preserves mathematical equations
4. Converts figures to LaTeX format
5. Generates compilable .tex file

**Commands executed:**

```bash
python .agent/skills/research-workflow/scripts/md_to_latex.py \
    research/scoliosis_theoretical_framework.md \
    --output manuscript/scoliosis.tex
```

**Result:**

- LaTeX manuscript ready for compilation
- Equations preserved in correct format
- Figures referenced with `\includegraphics`

---

### Example 3: Check Figure References

**User request:**

```
Check all figure references in the gravity paradox document
```

**What happens:**

1. Research-workflow skill activates
2. Runs `embed_figures.py` script
3. Lists all figure references
4. Validates file existence
5. Reports missing figures

**Commands executed:**

```bash
python .agent/skills/research-workflow/scripts/embed_figures.py \
    research/gravity_paradox_E_mc2.md \
    --figures-dir research/figures \
    --verbose
```

**Result:**

- Report showing all figures (✓ found, ✗ missing)
- List of available figures in directory
- Suggestions for fixes

---

## Document Skills

### Example 4: Create Word Document for Collaborator

**User request:**

```
Convert the scoliosis framework to a Word document for my biology collaborator
```

**What happens:**

1. docx skill activates
2. Reads research Markdown
3. Creates Word document with:
   - Formatted headings
   - Preserved equations (as images)
   - Embedded figures
   - Proper spacing and styles

**Result:**

- Professional Word document (`.docx`)
- Equations rendered clearly
- Figures properly embedded
- Ready to share with non-LaTeX users

---

### Example 5: Generate PDF with Comments

**User request:**

```
Create a PDF of the theoretical framework and add comments highlighting sections that need experimental validation
```

**What happens:**

1. pdf skill activates
2. Generates PDF from Markdown
3. Adds comment annotations at specified sections

**Result:**

- PDF with comment bubbles
- Highlighted sections for review
- Annotations preserved in standard PDF format

---

### Example 6: Create Presentation from Research

**User request:**

```
Create a 15-slide presentation from the scoliosis research for my conference talk
```

**What happens:**

1. pptx skill activates
2. Extracts key content from research document
3. Generates slides with:
   - Title slide
   - Introduction (2-3 slides)
   - Methods/Framework (3-4 slides)
   - Results with figures (3-4 slides)
   - Discussion (2 slides)
   - Conclusion (1 slide)

**Result:**

- Professional PowerPoint presentation
- Key equations highlighted
- Figures embedded
- Concise bullet points

**Follow-up customization:**

```
Make slide 4's equation larger and use a blue color scheme
```

---

## Doc Co-Authoring

### Example 7: Refine Research Document

**User request:**

```
I want to refine the introduction section of my scoliosis paper using the co-authoring workflow
```

**What happens:**

1. doc-coauthoring skill activates
2. Enters Stage 1: Context Gathering
   - Asks about target journal
   - Asks about audience
   - Requests any specific requirements
3. Enters Stage 2: Refinement
   - Brainstorms 10-15 points for introduction
   - User selects which to keep
   - Drafts refined introduction
   - Iteratively refines based on feedback
4. Enters Stage 3: Reader Testing
   - Tests with fresh Claude instance
   - Verifies clarity and completeness

**Result:**

- Polished introduction section
- Clear narrative flow
- Tested for reader comprehension

---

## Workflow Integration

### Example 8: Complete Manuscript Workflow

**User request:**

```
Follow the LaTeX conversion workflow for my research document
```

**What happens:**

1. Workflow guides step-by-step through:
   - Step 1: Prepare Markdown document
   - Step 2: Check figure references (auto-runs)
   - Step 3: Convert to LaTeX (auto-runs)
   - Step 4: Review LaTeX output  
   - Step 5: Add bibliography
   - Step 6: Generate PDF (auto-runs)
   - Step 7: Verify output

**Auto-run commands** (marked with `// turbo`):

```bash
# Step 2
python .agent/skills/research-workflow/scripts/embed_figures.py document.md --figures-dir research/figures

# Step 3  
python .agent/skills/research-workflow/scripts/md_to_latex.py document.md

# Step 6
python .agent/skills/research-workflow/scripts/generate_pdf.py manuscript.tex --clean
```

**Result:**

- Complete manuscript pipeline executed
- PDF generated from Markdown source
- All intermediate files created
- Ready for submission

---

### Example 9: Figure Management Workflow

**User request:**

```
Organize and validate all figures in my research directory
```

**What happens:**

1. figure-management workflow activates
2. Guides through:
   - Organize figures with descriptive names
   - Document metadata in figures/README.md
   - Check references in all documents
   - Validate file quality
   - Optimize file sizes

**Result:**

- Well-organized figure directory
- Documentation of each figure
- Validated references
- Optimized file sizes

---

### Example 10: Create Presentation Workflow

**User request:**

```
Create a conference presentation from my gravity paradox research
```

**What happens:**

1. create-presentation workflow activates
2. Guides through:
   - Identify scope (20 min → ~20 slides)
   - Outline structure
   - Extract content from research
   - Create slides using pptx skill
   - Customize design
   - Add formulae and figures
   - Review and iterate

**Result:**

- Professional presentation
- Proper pacing and structure
- Figures and equations readable
- Ready for conference

---

## Combining Skills

### Example 11: End-to-End Research Publication

**Complete workflow combining multiple skills:**

```
Create a complete research package for my scoliosis work: manuscript PDF, Word version for collaborators, and conference presentation
```

**What happens:**

1. **LaTeX conversion** (research-workflow + LaTeX workflow)
   - Convert Markdown → LaTeX
   - Generate publication PDF

2. **Word document** (docx skill)
   - Create Word version from Markdown
   - Add tracked changes enabled

3. **Presentation** (pptx skill + create-presentation workflow)
   - Extract key points
   - Generate slides
   - Embed figures

**Result:**

- `manuscript/scoliosis.pdf` - For journal submission
- `manuscript/scoliosis.docx` - For collaborators
- `presentation/scoliosis_talk.pptx` - For conference
- All from single source (Markdown)

---

## Tips for Effective Skill Usage

### Be Specific

Instead of: *"Help with my document"*  
Try: *"Convert scoliosis_theoretical_framework.md to LaTeX and generatePDF"*

### Reference Workflows

Instead of: *"I need to make a presentation"*  
Try: *"Follow the create-presentation workflow for gravity_paradox research"*

### Combine Skills

Instead of: Multiple separate requests  
Try: *"Create Word doc with track changes using docx skill, then co-author refinements using doc-coauthoring skill"*

### Use Domain Knowledge

Instead of: Explaining Cosserat theory each time  
Try: *"Use the domain knowledge reference for Cosserat rod notation"*

---

## Common Patterns

### Pattern 1: Research → Publication

1. Create research document (research-workflow skill)
2. Refine content (doc-coauthoring skill)
3. Convert to LaTeX (md_to_latex.py)
4. Generate PDF (generate_pdf.py)

### Pattern 2: Research → Collaboration

1. Create Markdown version (research-workflow skill)
2. Convert to Word (docx skill)
3. Enable track changes for review

### Pattern 3: Research → Presentation

1. Extract key points (manually or with doc-coauthoring)
2. Create slides (pptx skill)
3. Embed figures (figure-management workflow)

### Pattern 4: Multi-Format Distribution

1. Source: Markdown document
2. LaTeX → PDF for publication
3. docx for Word users
4. pptx for presentations
5. All from single source!
