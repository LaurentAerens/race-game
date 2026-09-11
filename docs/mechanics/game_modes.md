# Difficulty Settings

The game offers five difficulty levels. You can set this when starting a new career.

---

## Multiplier Table

| Setting | Very Easy | Easy | Normal | Hard | Very Hard |
|---------|-----------|------|--------|------|-----------|
| Development gain | ×1.40 | ×1.20 | ×1.00 | ×0.85 | ×0.70 |
| Driver growth | ×1.50 | ×1.25 | ×1.00 | ×0.80 | ×0.65 |
| Sponsor income | ×1.50 | ×1.25 | ×1.00 | ×0.80 | ×0.65 |
| Upkeep costs | ×0.70 | ×0.85 | ×1.00 | ×1.25 | ×1.50 |
| AI pace | ×0.93 | ×0.97 | ×1.00 | ×1.03 | ×1.06 |
| Innovation pitch rate | ×1.50 | ×1.25 | ×1.00 | ×0.75 | ×0.50 |
| Innovation success chance | ×1.30 | ×1.15 | ×1.00 | ×0.85 | ×0.70 |
| Innovation knowledge gain | ×1.30 | ×1.15 | ×1.00 | ×0.85 | ×0.70 |
| Negative penalty severity | ×0.60 | ×0.80 | ×1.00 | ×1.30 | ×1.60 |
| Starting cash bonus | +$5M | +$2.5M | $0 | −$2M | −$4M |

> [!NOTE]
> **Factory costs, parts costs, and R&D costs do not change between difficulties.** Only income rates, growth rates, AI speed, and penalty severity are scaled.

---

## How Scaling Works

Gains and penalties are scaled separately:

- **Positive outcomes** (development gains, innovation progress) × `dev_gain_mult`
- **Negative outcomes** (penalties, bad events) × `negative_penalty_mult`

On Very Easy, you get 40% more from good decisions and suffer only 60% of the usual penalty from bad ones. On Very Hard, those are reversed.

---

## Recommendations

| Experience level | Suggested difficulty |
|-----------------|---------------------|
| First playthrough | Easy or Normal |
| Familiar with all systems | Normal or Hard |
| Experienced player seeking a challenge | Hard or Very Hard |
| Just want to enjoy the story | Very Easy |
