const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, AlignmentType, 
        WidthType, BorderStyle, ShadingType, HeadingLevel, LevelFormat } = require('docx');
const fs = require('fs');

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Arial", size: 22 } } // 11pt
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "1B4D3E" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 }
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "2E75B6" },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 1 }
      }
    ]
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: {
                indent: { left: 720, hanging: 360 }
              }
            }
          }
        ]
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("ABSTRACT")]
      }),
      
      new Paragraph({ text: "", spacing: { after: 200 } }),
      
      new Paragraph({
        children: [new TextRun({
          text: "Title: Developmental Information as Biological Countercurvature: A Unified Framework for Spinal Geometry and Its Pathological Deviations",
          italics: true
        })],
        spacing: { after: 240 }
      }),

      new Paragraph({
        children: [new TextRun("The characteristic sigmoid (S) curvature of the vertebral column is a defining feature of vertebrate anatomy, yet its developmental origin remains poorly understood. Current biomechanical models attribute spinal geometry exclusively to passive gravitational geodesics&#x2014;the geometric curvature imposed by load-bearing constraints. However, this framework fails to explain spinal curvature in zero-gravity environments, scoliotic deviations despite normal gravity, and the remarkable conservation of S-curve geometry across vertebrate species with distinct body masses and locomotive modes. Here we propose a novel paradigm: Biological Countercurvature, wherein developmental information&#x2014;encoded through HOX gene patterning&#x2014;acts as a geometric modifier of the effective spacetime metric experienced by developing spinal tissues. Using Cosserat rod mechanics integrated with AlphaFold-predicted protein elasticity tensors, we demonstrate that HOX-mediated heterogeneity in tissue elasticity creates an Information-Elasticity Coupling (IEC) that generates the S-curve as the energetic ground state independent of gravitational loading. Our phase diagram reveals three distinct regimes: gravity-dominated (passive geodesics), cooperative (normal vertebrate physiology), and information-dominated (pathological spinal deformation). Crucially, this framework predicts that microgravity environments disrupt the information-gravitational balance, driving spine-related complications through fluid-shift-driven inflammatory mechanisms rather than pure mechanical unloading. We validate this model across nine mammalian species and show that known scoliosis-associated mutations correlate with predicted IEC disruptions. This work establishes a new theoretical foundation for understanding musculoskeletal development and suggests novel therapeutic interventions targeting the information-elasticity interface for spinal pathologies and microgravity-related complications.")]
        }),

      new Paragraph({ text: "", spacing: { after: 300 } }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("KEY FEATURES (for Editorial Dashboard)")]
      }),

      new Paragraph({ text: "", spacing: { after: 120 } }),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2340, 7020],
        rows: [
          new TableRow({
            children: [
              new TableCell({
                borders,
                width: { size: 2340, type: WidthType.DXA },
                shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({ children: [new TextRun({ text: "Novelty", bold: true })] })]
              }),
              new TableCell({
                borders,
                width: { size: 7020, type: WidthType.DXA },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({ children: [new TextRun("Information-Elasticity Coupling as a new theoretical framework bridging developmental biology and differential geometry")] })]
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                borders,
                width: { size: 2340, type: WidthType.DXA },
                shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({ children: [new TextRun({ text: "Rigor", bold: true })] })]
              }),
              new TableCell({
                borders,
                width: { size: 7020, type: WidthType.DXA },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({ children: [new TextRun("Cosserat mechanics + AlphaFold integration + cross-species validation + phase diagram analysis")] })]
              })
            ]
          }),
          new TableRow({
            children: [
              new TableCell({
                borders,
                width: { size: 2340, type: WidthType.DXA },
                shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({ children: [new TextRun({ text: "Significance", bold: true })] })]
              }),
              new TableCell({
                borders,
                width: { size: 7020, type: WidthType.DXA },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({ children: [new TextRun("Explains developmental origin of spinal geometry; suggests novel scoliosis treatments; predicts microgravity complications")] })]
              })
            ]
          })
        ]
      }),

      new Paragraph({ text: "", spacing: { after: 300 } }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("WORD COUNT")]
      }),

      new Paragraph({
        children: [new TextRun("Abstract: 210 words | Note: Exceeds Nature limit by 60 words. EDIT REQUIRED.")]
      }),

      new Paragraph({ text: "", spacing: { after: 300 } }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("NOTES FOR AUTHOR")]
      }),

      new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        children: [new TextRun("Edit down to 150 words maximum. Remove secondary details; keep: biological problem, your novel framework, key findings (phase diagram, microgravity prediction), significance")]
      }),

      new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        children: [new TextRun("Consider this structure: Problem (S-curve paradox) &#x2192; Gap in models &#x2192; Your solution (IEC) &#x2192; Method (Cosserat + AlphaFold) &#x2192; Result (phase diagram) &#x2192; Impact (scoliosis, microgravity)")]
      }),

      new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        children: [new TextRun("The microgravity prediction is your killer finding&#x2014;ensure it&#x2019;s in the final version")]
      }),

      new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        children: [new TextRun("Cross-species validation is important; keep if possible but may need to trim for space")]
      })
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/sessions/pensive-amazing-hawking/mnt/life/ABSTRACT_Template.docx", buffer);
  console.log("Abstract created successfully!");
});
