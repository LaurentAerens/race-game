# Innovation System

The Innovation Manager generates R&D breakthroughs through two types of pitches: in-house creative inventions and competitor intelligence. Both increase your car components' knowledge range, directly improving performance.

---

## How Innovation Works

When a pitch succeeds, **both `knowledge_min` and `knowledge_max` increase by the knowledge gain** for all targeted components on both Car 1 and Car 2. This expands the range in which your parts can perform, feeding into in-season R&D.

You can have a **maximum of 4 pitches pending** at any time. Greenlighting a pitch:
1. Deducts the cost immediately
2. Locks the relevant factory sub-department for the research duration
3. Resolves as success or failure at the end of the lockout period

---

## Type 1 — Creative Inventions (In-House)

Your engineering staff generate ideas for novel technical solutions.

**Pitch probability per week:**
```
P = (1 / 240) per staff member × rate_mult
```
For a typical 24-person team: ~9.6% chance of a new pitch per week.

**Knowledge gain:** 35–250 (varies by template). Higher-gain pitches are rarer and riskier.

**Success chance:**
```
base_chance = 12% (small gain) → 3% (large gain)   [inverse of magnitude]
+ factory bonuses
Clamped: 2% minimum, 75% maximum
```

**Cost:** `base_cost × (knowledge_gain / 100) × cost_mult`
High-gain pitches cost significantly more.

**Lockout duration:** 2–5 weeks. The relevant facility sub-department cannot progress during lockout.

### Factory Bonuses to Success Chance

| Facility | Bonus |
|---------|-------|
| CAD Office | +5% per tier |
| Rapid Prototyping | +8% per tier |
| QA / NDT Lab | +6% per tier |
| CFD Suite | +4% per tier |
| Wind Tunnel | +4% per tier |

> [!TIP]
> A Rapid Prototyping facility at T3 alone adds +24% success chance. Invest in your factory before greenlighting high-risk pitches.

---

## Type 2 — Competitor Intelligence (Trackside)

Your trackside crew monitors and analyses rival cars.

**Pitch probability:**
```
P = min(0.95, (0.15 + (trackside_crew / 20) × 0.35) × rate_mult × intel_roll_mult)
intel_roll_mult = 1.0 + (rival_intel_tier × 0.40) + (telephoto_eq_lvl × 0.10)
```

**Knowledge gain:** 10–30 per pitch (smaller, but much more reliable).

**Success chance:** 45–65% baseline, up to 95% cap. Much higher than creative inventions.

**Cost:** `base_cost × cost_mult` (not scaled by knowledge gain magnitude).

**Lockout duration:** 1–3 weeks. Reduced by 1 week if Reverse Engineering is T2 or Photogrammetry AI equipment is at level ≥ 2.

### Trackside Bonuses to Success Chance

| Facility / Equipment | Bonus |
|---------------------|-------|
| Rival Intelligence facility | +6% per tier |
| Reverse Engineering | +5% per tier |
| Telemetry | +3% per tier |
| Pit Rig | +2% per tier |
| Acoustic Microphones | +2% per equipment level |
| Wheel Guns | +1.5% per tier |

---

## Comparison

| | Creative Inventions | Competitor Intelligence |
|---|---|---|
| Knowledge gain | 35–250 | 10–30 |
| Base success chance | 3–12% | 45–65% |
| Max success chance | 75% | 95% |
| Cost scaling | By knowledge gain | Fixed |
| Lockout | 2–5 weeks | 1–3 weeks |
| Best for | Big breakthroughs | Steady incremental progress |

---

## Strategy

- **Mix both types.** Use competitor intelligence for reliable weekly gains. Queue creative pitches when you have strong factory bonuses and can absorb the risk of failure.
- **Never let all 4 slots be idle.** Even low-gain intelligence pitches compound across a full season.
- **High-gain creative pitches (200+ knowledge)** have a baseline success rate below 5%. Only greenlight them if your CAD, Rapid Proto, and QA facilities are well upgraded.
- **Lockout timing matters.** Avoid greenlighting a pitch with a long lockout right before you need that facility for another purpose.
