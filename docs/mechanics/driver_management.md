# Driver Management

---

## Driver Attributes

Every driver has **11 attributes** on a scale of 0–99. Each has a **potential ceiling** (`pot_pace`, `pot_braking`, etc.) — a stat can never exceed its potential.

### Driving Stats (8)

| Attribute | What it affects |
|-----------|----------------|
| `pace` | Raw single-lap speed |
| `race_starts` | Performance off the line and in early laps |
| `braking` | Braking-zone performance; important on technical circuits |
| `tire_management` | How gently the driver treats tyre compounds |
| `defending` | Ability to hold position under pressure |
| `wet_weather` | Performance in rain or mixed conditions |
| `consistency` | Race-to-race variance (high = predictable, low = volatile) |
| `fuel_efficiency` | Reduces fuel consumption during the race |

### Mental Stats (3 — can only increase, never decline)

| Attribute | What it affects |
|-----------|----------------|
| `technical_understanding` | Debrief quality, setup feedback |
| `communication` | Engineering relationship quality |
| `marketability` | Fan Club revenue and sponsor appeal |

---

## Driver Types

| Type | Salary | Contract length | Special mechanic |
|------|--------|----------------|-----------------|
| **STANDARD** | Market-rate based on tier + car rank | 1–5 seasons | Normal talent |
| **PAY_DRIVER** | Accepts any salary ≥ $0 | Negotiable | Brings **sponsor income** — weaker driver = larger sponsor deal |
| **SPONSORED_DRIVER** | $0 (team pays a seat fee) | 1 season only | On loan from parent constructor's academy. Gets development boost from parent team's tier. |

**Pay-driver sponsor income scaling:**
```
deficiency_boost = 1.0 + ((base_skill − current_skill) / base_skill) × 1.5
```
A low-skill pay-driver brings significantly more cash than a high-skill one.

---

## Contract Negotiation

Driver contract offers are evaluated with this scoring formula:

```
score = (salary_ratio × 0.60 + bonus_ratio × 0.40) × role_mult × seasons_mult
Accept threshold: score ≥ 0.95
```

**Role multipliers:**

| Situation | Multiplier |
|-----------|-----------|
| Driver expects #1 seat, offered #2 | 0.55× |
| Driver expects #1, offered equal | 0.88× |
| Driver offered #1 seat | 1.18× |

**Preference multipliers:**

| Driver preference | Condition | Multiplier |
|-----------------|-----------|-----------|
| SHORT_TERM | Offered > 2 seasons | 0.80× |
| LONG_TERM | Offered < 3 seasons | 0.80× |
| BONUS_SEEKER | Any | salary ratio ×0.85, bonus ratio ×1.30 |

**Car rank effect:** Top car (rank 1) reduces salary demands by 32%. Bottom car (rank 10) adds 40% to demands.

**Homegrown loyalty discount:** Academy-developed drivers who sign with your main team get a salary discount:
```
discount = max(0, 0.80 − min(6, seasons_at_main_team) × 0.16)
```
Starts at 80% discount, decays to 0% over 6 seasons.

> [!CAUTION]
> Each rejected offer decrements a driver's **patience** by 1. When patience hits 0, the driver walks away permanently and will not negotiate again.

---

## Driver Development

### Growth Phase (age ≤ 28)

Each week, race drivers gain stats based on:

```
growth = 0.38 × age_factor × pos_mult × tier_mult × fac_mult × driver_growth_mult × stat_mult
```

| Factor | Details |
|--------|---------|
| `age_factor` | `max(0.18, 1.0 − ((age−15)/14) × 0.55)` — youngest drivers grow fastest |
| `pos_mult` | P1 = 3.0× / P2-3 = 2.2× / P4-6 = 1.6× / P7-10 = 1.2× / P11-16 = 0.85× / P17+ = 0.55× |
| `tier_mult` | T1 = 1.35× / T2 = 1.20× / T3 = 1.10× / T4 = 1.00× / T5 = 0.90× |
| `fac_mult` | `1.15 × motion_xp_mult`; `motion_xp_mult = 1.0 + (motion_tier × 0.25) + (motion_eq × 0.04)` |
| `driver_growth_mult` | Scaled by difficulty setting |

### Plateau Phase (age 28–30)

No growth, no decline.

### Decline Phase (age > 30)

```
decay = 0.18 × ((age − 30) ^ 0.80) × decay_buffer
decay_buffer = max(0.15, 1.0 − (physio_tier × 0.35) − (physio_eq × 0.06))
```

Minimum stat floor: **20.0** — stats cannot fall below this. Upgrade your Physio facility and equipment to slow decline.

### Mental Stats

Mental stats (technical_understanding, communication, marketability) **never decline**. They grow at:
```
mental_growth = 0.25 × pos_mult × tier_mult × driver_growth_mult × m_stat_mult
```

---

## Facility Bonuses to Development

Specific facilities boost specific stats:

| Driver stat(s) | Facility |
|---------------|---------|
| `race_starts`, `defending`, `consistency` | VR Simulator (tier + equipment level) |
| `tire_management`, `wet_weather` | Gym (tier + equipment level) |
| `marketability` | Media Center + Communications Suite |
| `communication`, `technical_understanding` | Radio / Debrief Room |

---

## Academy Feeder System

Buy seats in the T4 or T5 feeder series to develop young talent:

- Academy drivers must be **aged ≤ 25** — they are automatically released at age > 25
- Monthly seat costs: T3 = $95k, T4 = $55k, T5 = $25k
- Academy weekly growth is faster than race drivers (base 0.52× vs 0.38×):

```
growth = 0.52 × age_factor × feeder_pos_mult × feeder_tier_mult × driver_growth_mult × bootcamp_mult × prodigy_mult
```

**Feeder pos_mult:** P1 = 3.2× / P2-3 = 2.4× / P4-6 = 1.8× / P7-10 = 1.3× / P11-16 = 0.9× / P17+ = 0.65×

**Prodigy condition:** If `age ≤ prodigy_max_age` AND `potential ≥ prodigy_threshold`, an additional prodigy multiplier applies:
```
prodigy_mult = 1.05 + (facility_count × facility_synergy_boost_rate × 1.5)
```

**bootcamp_mult:** `1.0 + (bootcamp_tier × 0.35) + (bootcamp_eq × 0.05)`

Graduating a driver from your academy to your main team activates the **loyalty discount** on their first contract (up to 80% off).
