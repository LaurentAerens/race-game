# UI Overview

This page describes every major UI component visible during a race session.

---

## Broadcast Header (Top Bar)

A permanent bar across the top of the screen. Always visible during races.

| Zone | Content |
|------|---------|
| **Left** | Circuit name + flag status badge (color-coded: Green / Yellow / SC / VSC / Red / Chequered) |
| **Centre-left** | Lap counter `LAP X / Y` and race elapsed time |
| **Centre** | Weather radar panel |
| **Right** | Camera toggle + simulation speed controls |

### Weather Radar (Centre Panel)

- Displays **track wetness %** and **track temperature**
- If a local shower is active: shows **per-sector wetness** (S1 / S2 / S3 independently)
- **Mini forecast bars:** one bar per upcoming lap. Minimum 6 laps shown, up to 10 depending on `radar_tier + radar_eq_lvl`
- Radar border turns **cyan** if a Weather Station facility is active
- Tag `[DOPPLER]` appears if the Weather Station is installed

### Camera & Speed Controls (Right)

- **CAM: CAR / CAM: OVERVIEW** — toggle between following a car and overview camera
- **|| 1x 2x 4x 8x** — simulation speed controls
- **F8 / F9** — UI zoom scale (a brief toast notification confirms the change)

---

## Timing Tower (Left Panel)

A permanent panel on the left during races. Shows all competitors.

**Columns:** `POS | DRIVER | GAP | TYRE | PIT`

| Element | Details |
|---------|---------|
| Driver code | Player car shown in **cyan**. Camera-followed car has a **blue background**. |
| Team livery | Color strip on the left edge of each row |
| GAP | `LEADER` for P1 · `+XX.Xs` for others · `DNF` if retired · `OFF` if off-track |
| TYRE | Colored dot (compound color) + compound code (1–2 chars) + wear % (red if < 40%) |
| PIT | `PIT` = currently in pit lane · `BOX` = boxing next lap · `OUT` = DNF · `XP` = pit stop count |

> [!TIP]
> **Clicking any row** in the Timing Tower switches the camera to follow that car.

Shows up to 20 cars.

---

## Driver Strategy Panel (Bottom)

One card per player-controlled car (maximum 2 cards side by side).

### Each Card Shows

- Current position, car number, driver name, driving style
- `[FLAG LOCKED]` badge when under Safety Car or VSC

### Left Column — Telemetry

| Reading | Notes |
|---------|-------|
| **FUEL** | Current fuel load in kg |
| **ERS** | T1: percentage + active mode · T2: percentage + `[Spec]` · T3: `N/A` |
| **TYRE** | Wear % + compound name in compound color |

### Centre — Control Buttons

| Row | Buttons | Tier restrictions |
|-----|---------|------------------|
| **PACE** | CONS · NORM · PUSH · ATK | CONS and ATK locked (greyed) in T3 |
| **ENGINE** | LEAN · STD · RICH | LEAN and RICH locked in T3 |
| **ERS** | AUTO · RCHG · BAL · BOOST | Shows `----` in T3 |

All buttons are locked while a flag condition (SC / VSC / Yellow) is active.

### Right — BOX Button

Opens the **Pit Strategy Modal**. Turns red when a pit stop is already queued — click again to cancel.

### Bottom — Component Health Bar

`FW XX% | RW XX% | BRK XX% | ENG XX%`

Color coding: **green ≥ 50%** · **orange 30–50%** · **red < 30%**

---

## Pit Strategy Modal

A 460×360 px overlay that appears when you call a pit stop.

**Title:** `PIT STRATEGY — [Driver Name] (#[Number])`

| Section | Details |
|---------|---------|
| Compound cards (5) | Dry variants + INTER + WET. Shows name, tier, grip %, cliff wear %. |
| Selected compound info | Name, tier, grip %, cliff wear % in a highlight bar |
| Front Wing Replacement | Toggle. `+4.0 s`. Greyed out with `NO SPARE IN STOCK` if warehouse is empty. Shows spare durability %. |
| Emergency Repairs | Toggle. `+14.0 s`. Patches all parts below 55% durability to random 55–60%. |
| Estimated stop time | Calculated forecast shown before you confirm. |
| Part health strip | Current durability of all components. |
| CONFIRM / ABORT | Green to confirm, red to abort. ESC or clicking outside also closes. |

---

## Radio Banner

Short messages from your race engineer appear as brief banners during the race (powered by the radio system). No separate "Event Feed" panel — all communications appear as transient banners.

---

## Management Hub

The full off-race management interface covering: Factory, Engineering, Drivers, Staff, Sponsors, Innovation, and Academy. Not accessible during live race sessions.
