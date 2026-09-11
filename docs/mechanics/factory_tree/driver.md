# Driver Performance Department

The Driver Performance department develops your race drivers and academy prospects. Facilities here directly multiply the weekly stat growth applied after each race and slow the decline of aging drivers.

---

## Tree Structure

```
Driver Sim Rig ($2.3M)                  ← ROOT
├── Biometric Gym ($9.5M)              → Tire Management, Wet Weather
│   └── Physio Clinic ($17M)           → slows age 30+ decline
├── Media & PR Studio ($10.5M)         → Marketability
│   ├── Radio Comms Lab ($14M)         → Communication, Technical Understanding; +R&D insight
│   └── Sponsor Suite ($18.5M)         → +Sponsor appeal & race bonus
├── Driver Academy ($16M)              → feeder seat purchases
│   └── Karting Foundation ($19M)      → T5 talent radar; prodigy guarantee
│       └── Junior Boot Camp ($24M)    → feeder driver XP +35%
└── Hexapod Sim ($26M)                 → +50% driver XP (all stats)
    └── Neuro-Reflex Lab ($13.5M)      → Race Starts, Defending, Consistency
```

---

## Node Reference

### Driver Sim Rig
| Field | Value |
|-------|-------|
| Node ID | `driver_sim` |
| Build cost | $2,300,000 |
| Monthly upkeep | $72,000 × tier |
| Staff capacity | 6 / 12 / 18 |
| Prerequisite | None (root node) |

Driver track familiarity training and baseline reflexes. The entry to all driver development. Buy early — it feeds `motion_xp_mult` which scales all race driver growth:
`motion_xp_mult = 1.0 + (motion_tier × 0.25) + (motion_eq × 0.04)`

At T3 with equipment: `motion_xp_mult = 1.75 + eq_bonus`, meaning a **75% base driver growth bonus** from this single node.

---

### Biometric Gym
| Field | Value |
|-------|-------|
| Node ID | `driver_gym_conditioning` |
| Build cost | $9,500,000 |
| Monthly upkeep | $275,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | Driver Sim Rig |
| Effect | `tire_management` and `wet_weather` weekly growth: +`(gym_tier × 0.25) + (gym_eq × 0.04)` per week |

G-force neck harnesses and sauna heat chambers. Directly boosts the two physical endurance stats. Essential on rain-heavy circuits (high `wet_weather` demand) and for strategy that relies on pushing tyres hard.

---

### Physio Clinic
| Field | Value |
|-------|-------|
| Node ID | `driver_physio_recovery` |
| Build cost | $17,000,000 |
| Monthly upkeep | $480,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Biometric Gym |
| Effect | `decay_buffer = max(0.15, 1.0 − (physio_tier × 0.35) − (physio_eq × 0.06))` — reduces age 30+ decline |

Cryotherapy and hyperbaric recovery chambers. For a driver aged 32 at T3 Physio: `decay_buffer = max(0.15, 1.0 − 1.05 − eq) = 0.15` — the minimum possible decay. Effectively halts most stat decline for older elite drivers. Critical if you have a high-rated driver you want to keep competitive into their mid-thirties.

---

### Media & PR Studio
| Field | Value |
|-------|-------|
| Node ID | `driver_media_pr_coach` |
| Build cost | $10,500,000 |
| Monthly upkeep | $300,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | Driver Sim Rig |
| Effect | `marketability` weekly growth: +`(media_tier × 0.35) + (media_eq × 0.05)` per week |

Paddock press simulation and crisis communication coaching. `marketability` scales Fan Club revenue (`rev = 10,000 × fc_tier × perf_factor × tier_econ × (avg_marketability / 50)`). Improving it has direct, compounding financial impact. Gateway to Radio Comms Lab and Sponsor Suite.

---

### Radio Comms Lab
| Field | Value |
|-------|-------|
| Node ID | `driver_radio_comms_lab` |
| Build cost | $14,000,000 |
| Monthly upkeep | $400,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Media & PR Studio |
| Effect | `communication` and `technical_understanding` weekly growth: +`(radio_tier × 0.35) + (radio_eq × 0.05)` per week; also adds `(radio_tier × 0.15) + (radio_eq × 0.03)` to `driver_factor` in post-race telemetry |

115dB cockpit acoustic simulation and telemetry debrief training. Improves both mental stats and boosts the driver's contribution to post-race R&D insight (driver_factor scales all telemetry knowledge gain).

---

### Sponsor Suite
| Field | Value |
|-------|-------|
| Node ID | `driver_commercial_suite` |
| Build cost | $18,500,000 |
| Monthly upkeep | $520,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Media & PR Studio |
| Effect | +5 Sponsor Appeal; +6%/tier on performance bonus payouts from sponsor contracts |

Brand ambassador stage and VIP lounges. Improves sponsor contract attractiveness and increases performance bonus multipliers.

---

### Driver Academy
| Field | Value |
|-------|-------|
| Node ID | `driver_academy` |
| Build cost | $16,000,000 |
| Monthly upkeep | $460,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Driver Sim Rig |

Unlocks the ability to **purchase seats in T4 and T5 feeder series** to develop academy drivers. Without this, you cannot run an academy program. Monthly seat costs: T5 = $25k, T4 = $55k, T3 = $95k.

---

### Karting Foundation
| Field | Value |
|-------|-------|
| Node ID | `driver_karting_scholarship` |
| Build cost | $19,000,000 |
| Monthly upkeep | $540,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Driver Academy |

Grassroots talent radar in Tier 5 Karting Masters Academy. Guarantees prodigy-quality scouting and raises the minimum potential floor by +4 for new academy prospects. Gateway to Junior Boot Camp.

---

### Junior Boot Camp
| Field | Value |
|-------|-------|
| Node ID | `driver_f4_bootcamp` |
| Build cost | $24,000,000 |
| Monthly upkeep | $680,000 × tier |
| Staff capacity | 14 / 28 / 42 |
| Prerequisite | Karting Foundation |
| Effect | `bootcamp_mult = 1.0 + (bootcamp_tier × 0.35) + (bootcamp_eq × 0.05)` added to all academy driver growth |

Single-seater test fleet and telemetry track camp. At T3: `bootcamp_mult = 2.05 + eq_bonus` — more than **doubles** academy driver development rate. Essential for any serious academy investment.

---

### Hexapod Sim
| Field | Value |
|-------|-------|
| Node ID | `driver_motion_sim` |
| Build cost | $26,000,000 |
| Monthly upkeep | $720,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Driver Sim Rig |
| Effect | `motion_xp_mult = 1.0 + (motion_tier × 0.25) + (motion_eq × 0.04)` — multiplicative on ALL driver stat growth |

Driver-in-the-Loop hexapod motion platform. The most powerful single driver development node — the motion multiplier applies to every driving stat, every week, for every race driver. Also gates the Neuro-Reflex Lab.

---

### Neuro-Reflex Lab
| Field | Value |
|-------|-------|
| Node ID | `driver_vr_cognitive` |
| Build cost | $13,500,000 |
| Monthly upkeep | $390,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | Hexapod Sim |
| Effect | `race_starts`, `defending`, `consistency` weekly growth: +`(vr_tier × 0.30) + (vr_eq × 0.05)` per week |

Batak reaction matrix and saccade tracking. Targets the three stats most affected by VR training. Consistency is particularly important — it determines race-to-race variance (`cons_factor = (100 - consistency) / 100`).
