const { Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel } = require('docx');
const fs = require('fs');

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Arial", size: 22 } } // 11pt
    }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      // Header
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun("Dr. Sayuj K.S.")],
        spacing: { after: 40 }
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun("hellodr@drsayuj.info")],
        spacing: { after: 40 }
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun("[Your Institution]")],
        spacing: { after: 40 }
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun("[Date]")],
        spacing: { after: 240 }
      }),

      // Recipient
      new Paragraph({
        children: [new TextRun("The Editor")],
        spacing: { after: 40 }
      }),
      new Paragraph({
        children: [new TextRun("Nature")],
        spacing: { after: 40 }
      }),
      new Paragraph({
        children: [new TextRun("4 Crinan Street")],
        spacing: { after: 40 }
      }),
      new Paragraph({
        children: [new TextRun("London N1 9XW, UK")],
        spacing: { after: 240 }
      }),

      // Salutation
      new Paragraph({
        children: [new TextRun("Dear Editor,")],
        spacing: { after: 240 }
      }),

      // Opening paragraph
      new Paragraph({
        children: [new TextRun("We submit for consideration in Nature a manuscript titled &#x201C;Developmental Information as Biological Countercurvature: A Unified Framework for Spinal Geometry and Its Pathological Deviations.&#x201D; This work presents a paradigm-shifting framework that bridges developmental biology, differential geometry, and biomechanics to explain one of vertebrate biology&#x2019;s most fundamental yet poorly understood phenomena: the origin of spinal curvature. We believe this manuscript represents a significant conceptual advance with broad implications for developmental biology, evolutionary biology, musculoskeletal medicine, and space physiology.")],
        spacing: { after: 240 }
      }),

      // Problem statement
      new Paragraph({
        children: [new TextRun({
          text: "The Biological Problem",
          bold: true
        })],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("The characteristic S-shaped (sigmoid) curvature of the vertebral column is a defining anatomical feature across vertebrate species. Yet despite over a century of biomechanical study, the developmental origin of this geometry remains mysterious. Current models attribute spinal curvature solely to passive gravitational geodesics&#x2014;the geometrical curves that emerge when flexible structures conform to gravitational loading. However, this framework faces critical failures: (1) Spinal curvature persists in microgravity environments, where gravitational loading is absent. (2) Scoliotic deformations occur despite normal gravitational fields, suggesting an alternative organizing principle. (3) The S-curve geometry is conserved across vertebrate species with dramatically different body masses, sizes, and locomotive strategies&#x2014;an improbable coincidence if gravity alone determined spinal shape.")],
        spacing: { after: 240 }
      }),

      // Our solution
      new Paragraph({
        children: [new TextRun({
          text: "Our Novel Framework: Biological Countercurvature",
          bold: true
        })],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("We propose that developmental information&#x2014;encoded through HOX gene patterning along the rostrocaudal axis&#x2014;acts as a &#x201C;countercurvature,&#x201D; geometrically modifying the effective spacetime metric experienced by developing spinal tissues. By integrating Cosserat rod mechanics with AlphaFold-predicted protein structures, we demonstrate that HOX-mediated heterogeneity in tissue elasticity (the Information-Elasticity Coupling, or IEC) can generate the S-curve as an energetic ground state independent of gravitational loading. This framework predicts three distinct regimes: (1) gravity-dominated (observed in small aquatic organisms), (2) cooperative (normal mammalian physiology), and (3) information-dominated (pathological spinal deformation). Critically, our model predicts that microgravity disrupts the information-gravitational balance, shifting dynamics toward fluid-shift-driven inflammatory mechanisms&#x2014;a testable prediction with implications for astronaut health.")],
        spacing: { after: 240 }
      }),

      // Validation
      new Paragraph({
        children: [new TextRun({
          text: "Evidence & Validation",
          bold: true
        })],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("We validate this framework across nine mammalian species (ranging from mice to whales), demonstrating quantitative agreement between predicted IEC-based curvature and observed spinal geometry. We further show that genetic mutations known to cause scoliosis correlate with predicted disruptions to the information-elasticity interface. The model&#x2019;s prediction of microgravity-specific complications provides a mechanistic explanation for observed space-flight spinal changes and suggests interventions based on information-elasticity dynamics rather than simple mechanical unloading counters.")],
        spacing: { after: 240 }
      }),

      // Significance
      new Paragraph({
        children: [new TextRun({
          text: "Significance & Scope",
          bold: true
        })],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("This work has implications across multiple domains: (1) "),
          new TextRun({ text: "Developmental Biology:", bold: true }),
          new TextRun(" Establishes how genetic information physically shapes form during development. (2) "),
          new TextRun({ text: "Evolutionary Biology:", bold: true }),
          new TextRun(" Explains the robust emergence of S-curve morphology across diverse vertebrate lineages. (3) "),
          new TextRun({ text: "Clinical Medicine:", bold: true }),
          new TextRun(" Identifies the information-elasticity interface as a therapeutic target for scoliosis and other musculoskeletal disorders. (4) "),
          new TextRun({ text: "Space Physiology:", bold: true }),
          new TextRun(" Predicts and may help mitigate spinal complications in long-duration spaceflight. This work unifies previously disconnected literatures and opens new avenues for both fundamental science and therapeutic intervention.")],
        spacing: { after: 240 }
      }),

      // Originality & Scope
      new Paragraph({
        children: [new TextRun({
          text: "Originality & Scope",
          bold: true
        })],
        spacing: { after: 120 }
      }),
      new Paragraph({
        children: [new TextRun("This work is original and has not been submitted for publication elsewhere. It represents a significant conceptual advance over prior work in biomechanics, developmental biology, and mathematical biology. The interdisciplinary nature of this work&#x2014;bridging physics, genetics, and medicine&#x2014;aligns well with Nature&#x2019;s scope and audience.")],
        spacing: { after: 240 }
      }),

      // Closing
      new Paragraph({
        children: [new TextRun("We would be delighted to address any questions from the editorial office. We are prepared to provide supplementary materials, code repositories, and additional data as needed. We suggest the following potential reviewers:")],
        spacing: { after: 120 }
      }),

      new Paragraph({
        numbering: { reference: "numbers", level: 0 },
        children: [new TextRun("[Suggested Reviewer 1: Spinal biomechanist]")]
      }),
      new Paragraph({
        numbering: { reference: "numbers", level: 0 },
        children: [new TextRun("[Suggested Reviewer 2: Developmental biologist specializing in HOX genes]")]
      }),
      new Paragraph({
        numbering: { reference: "numbers", level: 0 },
        children: [new TextRun("[Suggested Reviewer 3: Mathematical biologist working on morphogenesis]")]
      }),
      new Paragraph({
        numbering: { reference: "numbers", level: 0 },
        children: [new TextRun("[Suggested Reviewer 4: Space life scientist studying microgravity effects]")]
      }),
      new Paragraph({
        numbering: { reference: "numbers", level: 0 },
        children: [new TextRun("[Suggested Reviewer 5: Clinician/researcher in scoliosis treatment]")]
      }),

      new Paragraph({ text: "", spacing: { after: 240 } }),

      new Paragraph({
        children: [new TextRun("Thank you for your consideration. We look forward to hearing from you.")],
        spacing: { after: 240 }
      }),

      new Paragraph({
        children: [new TextRun("Sincerely,")],
        spacing: { after: 120 }
      }),

      new Paragraph({
        children: [new TextRun([new TextRun("")])],
        spacing: { after: 120 }
      }),

      new Paragraph({
        children: [new TextRun("Dr. Sayuj K.S.")],
        spacing: { after: 40 }
      }),

      new Paragraph({
        children: [new TextRun("hellodr@drsayuj.info")],
        spacing: { after: 240 }
      }),

      // Footer notes
      new Paragraph({
        children: [new TextRun({
          text: "NOTES FOR AUTHOR:",
          bold: true,
          italics: true,
          color: "666666",
          size: 18
        })],
        spacing: { after: 80 }
      }),
      new Paragraph({
        children: [new TextRun({
          text: "Replace [Your Institution] with your affiliation. Update [Date] with submission date. Replace [Suggested Reviewer X] with names of leading experts in each field. Ensure suggested reviewers do not have conflicts of interest with you. Remove these notes before submitting. Keep cover letter to ~500 words maximum.",
          italics: true,
          color: "666666",
          size: 18
        })]
      })
    ],
    numbering: {
      config: [
        {
          reference: "numbers",
          levels: [
            {
              level: 0,
              format: "decimal",
              text: "%1.",
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
    }
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/sessions/pensive-amazing-hawking/mnt/life/COVER_LETTER_Template.docx", buffer);
  console.log("Cover letter created successfully!");
});
