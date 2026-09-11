# Commercial Department

The Commercial department builds your brand presence and generates the five performance-scaled revenue streams that supplement your base sponsor retainer. Each commercial node both increases `marketability` for your drivers and unlocks or scales one revenue channel.

---

## Tree Structure

```
Press & PR Office ($2.4M)              ← ROOT
├── Digital & Social ($7.8M)           → +8 Marketability
│   ├── Fan Club ($9.5M)               → Fan Club monthly revenue
│   └── Media Studio ($21M)            → +12 Marketability
│       └── Esports Rig ($13.5M)       → +6 Marketability
├── Brand & Livery ($8.5M)             → +6 Marketability, +5% Sponsor Value
│   ├── Merchandise ($11.5M)           → Merchandise monthly revenue
│   │   └── Brand Licensing ($16.5M)   → Licensing monthly revenue
│   │       └── Heritage Museum ($25M) → Museum/Heritage monthly revenue
│   └── VIP Hospitality ($29M)         → +10 Sponsor Appeal
│       └── Customer Racing ($65M)     → Customer Racing monthly revenue
```

---

## Revenue Formulas

All commercial streams scale with:
- `perf_factor = max(0.15, min(1.35, 1.45 − avg_recent_pos × 0.10))` (last 5 race results)
- `tier_econ`: T1=1.0, T2=0.65, T3=0.40, T4=0.20, T5=0.08

---

## Node Reference

### Press & PR Office
| Field | Value |
|-------|-------|
| Node ID | `mkt_press` |
| Build cost | $2,400,000 |
| Monthly upkeep | $70,000 × tier |
| Staff capacity | 6 / 12 / 18 |
| Prerequisite | None (root node) |
| Effect | +4 Marketability to all race drivers |

Media access, press releases, and sentiment management. A cheap, immediate marketability boost and the gateway to the entire commercial tree.

---

### Digital & Social
| Field | Value |
|-------|-------|
| Node ID | `mkt_digital` |
| Build cost | $7,800,000 |
| Monthly upkeep | $220,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | Press & PR Office |
| Effect | +8 Marketability |

Real-time social coverage and viral fan channels. Gateway to Fan Club and Media Studio.

---

### Fan Club
| Field | Value |
|-------|-------|
| Node ID | `mkt_fan_club` |
| Build cost | $9,500,000 |
| Monthly upkeep | $270,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | Digital & Social |
| Revenue | `$10,000 × fc_tier × perf_factor × tier_econ × (avg_marketability / 50)` per month |
| Effect | +5 Marketability |

Fan community, loyalty voting, and subscription dues. This revenue stream **directly scales with driver marketability** — the higher your average driver marketability, the more this generates. Combined with the Media & PR Studio (Driver Performance dept), marketability investment compounds here.

---

### Media Studio
| Field | Value |
|-------|-------|
| Node ID | `mkt_studio` |
| Build cost | $21,000,000 |
| Monthly upkeep | $580,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Digital & Social |
| Effect | +12 Marketability |

Soundstage, car launches, and docuseries production. Large marketability boost with no direct revenue of its own — value comes from the multiplier effect on fan club and sponsor appeal.

---

### Esports Rig
| Field | Value |
|-------|-------|
| Node ID | `mkt_esports` |
| Build cost | $13,500,000 |
| Monthly upkeep | $380,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Media Studio |
| Effect | +6 Marketability |

Factory sim racing team and streaming infrastructure.

---

### Brand & Livery
| Field | Value |
|-------|-------|
| Node ID | `mkt_brand_design` |
| Build cost | $8,500,000 |
| Monthly upkeep | $240,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | Press & PR Office |
| Effect | +6 Marketability, +5% Sponsor appeal value |

Livery styling and decal placement. Gateway to Merchandise and VIP Hospitality.

---

### Merchandise
| Field | Value |
|-------|-------|
| Node ID | `mkt_merch` |
| Build cost | $11,500,000 |
| Monthly upkeep | $320,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Brand & Livery |
| Revenue | `$12,000 × merch_tier × perf_factor × tier_econ` per month |
| Effect | +5 Marketability |

Official apparel and fan gear. Straightforward result-scaled revenue. Gateway to Brand Licensing.

---

### Brand Licensing
| Field | Value |
|-------|-------|
| Node ID | `mkt_licensing` |
| Build cost | $16,500,000 |
| Monthly upkeep | $450,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Merchandise |
| Revenue | `$8,000 × lic_tier × perf_factor × tier_econ × (reputation / 50)` per month |
| Effect | +6 Marketability |

Gaming CAD licenses and diecast model partnerships. Scales with **team reputation** in addition to performance factor.

---

### Heritage Museum
| Field | Value |
|-------|-------|
| Node ID | `mkt_heritage` |
| Build cost | $25,000,000 |
| Monthly upkeep | $680,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Brand Licensing |
| Revenue | `($8,000 + titles_won × $10,000) × museum_tier × max(0.5, perf_factor) × tier_econ` per month |
| Effect | +8 Marketability |

Championship trophy display and team history exhibit. Revenue **scales with championship titles** — each title won permanently adds $10,000 to the base. Uses `max(0.5, perf_factor)` so poor results still generate decent museum income.

---

### VIP Hospitality
| Field | Value |
|-------|-------|
| Node ID | `mkt_hospitality` |
| Build cost | $29,000,000 |
| Monthly upkeep | $780,000 × tier |
| Staff capacity | 14 / 28 / 42 |
| Prerequisite | Brand & Livery |
| Effect | +10 Sponsor Appeal; +6%/tier on sponsor performance bonus payouts |

Paddock Club suites and executive lounges. Improves sponsor contract appeal scores and multiplies sponsor performance bonuses. Gateway to Customer Racing.

---

### Customer Racing
| Field | Value |
|-------|-------|
| Node ID | `mkt_customer_racing` |
| Build cost | $65,000,000 |
| Monthly upkeep | $1,750,000 × tier |
| Staff capacity | 18 / 36 / 54 |
| Prerequisite | VIP Hospitality |
| Revenue | `$25,000 × cr_tier × perf_factor × tier_econ` per month |
| Effect | +15 Sponsor Appeal |

Retired championship chassis sales and VIP client track days. The highest monthly revenue rate per tier of any commercial node, and the largest sponsor appeal bonus. Also the most expensive commercial investment — only viable as a T1 end-game facility.
