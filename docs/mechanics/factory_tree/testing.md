# Testing Department

The Testing department focuses on structural validation, dynamic simulation, and quality assurance. These nodes provide some of the most impactful cross-cutting effects — especially the QA & NDT Lab which delivers a massive reliability gain across all 7 components.

> [!NOTE]
> All Testing nodes require **Tier 1** to unlock.

---

## Tree Structure

```
Suspension Shop (ENGINEERING)
└── Kinematics Rig ($12.5M)            → SUSP, BRK handling
    └── 7-Post Shaker Rig ($22M)       → SUSP, BRK, FLOOR kerb loads

Monocoque Jig (MANUFACTURING)
└── Torsional Rig ($16M)               → structural stiffness, rel gains on composites

Electronics Lab (MANUFACTURING)
└── QA & NDT Lab ($9M)                 → +35% rel ALL parts; −4% perf ALL parts
```

---

## Node Reference

### Kinematics Rig
| Field | Value |
|-------|-------|
| Node ID | `eng_kinematics_lab` |
| Build cost | $12,500,000 |
| Monthly upkeep | $360,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Suspension Shop (Engineering) |
| Effect | SUSP, BRK: +12%/tier Perf |

Roll centers, camber gain, and anti-dive motion simulation. Reduces tyre degradation by 6% and improves mechanical grip modeling for SUSP and BRK development. Gateway to the 7-Post Shaker Rig.

---

### 7-Post Shaker Rig
| Field | Value |
|-------|-------|
| Node ID | `test_shaker_rig` |
| Build cost | $22,000,000 |
| Monthly upkeep | $600,000 × tier |
| Staff capacity | 14 / 28 / 42 |
| Prerequisite | Kinematics Rig |
| Effect | SUSP, BRK, FLOOR: +15%/tier Perf |

Hydraulic multi-post rig replicating track surface bumps, kerb strikes, and aero heave loads. Stacks multiplicatively with the Kinematics Rig for suspension development. Also noted for +15% kerb grip improvement.

---

### Torsional Rig
| Field | Value |
|-------|-------|
| Node ID | `test_torsional_rig` |
| Build cost | $16,000,000 |
| Monthly upkeep | $440,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Monocoque Jig (Manufacturing) |
| Effect | FW, RW, FLOOR: −2%/tier Perf (conservative screening); SUSP, FLOOR: +14%/tier Rel |

Hydraulic load frames twisting bare tubs for structural stiffness testing. Trades a slight aerodynamic performance penalty (conservative design screening) for a significant reliability gain on composites and suspension. Combined with QA & NDT Lab, this makes composite parts extremely durable.

---

### QA & NDT Lab
| Field | Value |
|-------|-------|
| Node ID | `test_qa_ndt` |
| Build cost | $9,000,000 |
| Monthly upkeep | $260,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Electronics Lab (Manufacturing) |
| Effect | **All 7 components: −4%/tier Perf, +35%/tier Rel** |

> [!TIP]
> This is the most impactful reliability node in the entire factory. A Tier 3 QA & NDT Lab adds **+105% reliability multiplier** across all 7 car components every race. The small performance screening penalty (−12% at T3) is almost always worth it.

Ultrasonic defect detection and failure-mode prevention. Screens out bleeding-edge designs conservatively (-4% perf per tier), but prevents mechanical failures during race builds (+35% per tier to all component reliability knowledge).

Also directly shields against breakthrough innovation reliability penalties: if QA is built, breakthrough builds lose less reliability (`ndt_shield = ndt_tier × 1.5`).
