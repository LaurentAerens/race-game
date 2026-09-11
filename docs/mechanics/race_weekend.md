# Race Weekend

---

## Session Structure

Race weekends vary by tier:

| Session | Tier 3 | Tier 2 | Tier 1 |
|---------|--------|--------|--------|
| Free Practice 1 | ✅ 5 laps | ✅ 5 laps | ✅ 5 laps |
| Free Practice 2 | ✅ 5 laps | ✅ 5 laps | ✅ 5 laps |
| Qualifying | ✅ 3 laps | ✅ 3 laps | ✅ 3 laps |
| Sprint | ✅ | ❌ | ✅ (top-10 reversed grid) |
| Free Practice 3 | ❌ | ❌ | ✅ 5 laps |
| Race | ❌ | ✅ | ✅ |

**Lap counts:**
- Sprint: `max(7, round(circuit_base_laps × 0.38))`
- Race: `max(18, circuit_base_laps)`

---

## Free Practice

Each practice session is **5 laps**. Before the session you choose a **practice plan**:

| Plan | Purpose |
|------|---------|
| `FAST_LAP` | Maximise single-lap pace — feeds qualifying setup confidence |
| `LONG_RUNS` | Fuel saving and tyre deg data — unlocks fuel saving bonus in race |
| `SPRINT_STINTS` | Optimised for sprint-distance runs |
| `BALANCED` | General-purpose data gathering |

Practice builds **setup confidence**, which seeds the virtual simulation for the race. More practice laps on the correct plan = better setup for that session type.

---

## Pace Modes

Pace mode is set per car via the **Driver Strategy Panel**. Affects tyre and component wear:

| Mode | Wear Multiplier | Available In |
|------|----------------|--------------|
| CONSERVE | 0.70× | T2 and T1 only |
| NORMAL | 1.00× | All tiers |
| PUSH | 1.35× | All tiers |
| ATTACK | 1.80× | T2 and T1 only |

> [!WARNING]
> Pace mode is **locked** under Safety Car and VSC. Plan your strategy ahead of flag periods.

---

## Engine Modes

Engine mode affects fuel consumption and engine wear:

| Mode | Fuel Burn | Engine Wear | Available In |
|------|-----------|-------------|--------------|
| LEAN | 0.80× | 0.80× | T2 and T1 only |
| STANDARD | 1.00× | 1.00× | All tiers |
| RICH | 1.35× | 1.40× | T2 and T1 only |

Fuel starts at **50 kg** at race start. There is **no refueling** during pit stops. Fuel burn per tick:

```
fuel_burn = 0.018 × chassis_fuel_factor × fuel_bonus_mult × engine_mode_mult
chassis_fuel_factor = 1.15 - 0.30 × (driver_fuel_efficiency / 100)
```

A `LONG_RUNS` practice plan unlocks a fuel-saving bonus multiplier during the race.

---

## ERS (Energy Recovery System)

| Tier | ERS Status |
|------|-----------|
| T3 | Not available — shows `N/A` |
| T2 | Percentage shown, mode is `[Spec]` (not manually controlled) |
| T1 | Full control: AUTO / RECHARGE / BALANCED / OVERTAKE |

---

## Component Wear & Breakdowns

All components wear continuously during the race:

```
continuous_wear = 0.32 × pace_deg_mult × (distance_travelled / lap_distance)
```

Engine also applies the engine mode wear multiplier on top of pace deg mult.

> [!CAUTION]
> Any component reaching **0%** causes an **immediate terminal mechanical retirement**. Keep an eye on the health bars in the Driver Panel (FW / RW / BRK / ENG).

Emergency pit-stop repairs restore components below 55% to a random 55–60%.

---

## Race Flags

| Flag | Effect |
|------|--------|
| 🟡 Yellow | Sector caution. Pace mode change locked for that sector. |
| VSC | Full-course slow. All controls locked. |
| SC | Safety Car deployed. All controls locked. Gap to leader compresses. |
| 🔴 Red | Race suspended. |
| 🏁 Chequered | Session complete. |

Locking means you cannot change pace mode, engine mode, or ERS while the flag is active.

---

## DRS & Aerodynamics

- **DRS activates** when a driver is within **1.05 seconds** of the car ahead at the detection point.
- **Slipstream:** Following closely on a straight provides a drafting speed bonus.
- **Dirty Air:** Following through corners causes mechanical grip loss.

---

## Driver Styles

Each driver races with a characteristic style that affects their behaviour:

| Style | Character |
|-------|-----------|
| LATE_BRAKER | Carries more speed into braking zones |
| SMOOTH_ROLLER | Consistent, easy on tyres |
| TIRE_WHISPERER | Excellent tyre management |
| AGGRESSIVE_HUNTER | High attack in overtaking situations |
| BALANCED | No pronounced tendency |

---

## Weather

- Weather profiles: `SUNNY`, `RAIN`, `DYNAMIC` (changes during session).
- The **broadcast header** shows track wetness % and temperature. With a local shower, per-sector wetness (S1/S2/S3) is shown separately.
- Radar forecast bars show upcoming lap weather — minimum 6 laps ahead, up to 10 with a Weather Station facility (`[DOPPLER]` tag appears).
- **Rain chance varies by circuit** (examples): Knockhill 55%, Ardennes 60%, Vortex 40%, Riviera 18%, Harbor 12%, Oasis 2%.
- Wet weather skill (`wet_weather` driver stat) becomes a major performance factor in the rain.
