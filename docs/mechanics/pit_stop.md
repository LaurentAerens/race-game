# Pit Stops

---

## Calling a Pit Stop

Click the **BOX** button on a car's card in the **Driver Strategy Panel** (bottom of screen). This opens the **Pit Strategy Modal**, where you configure the stop before confirming.

While a stop is queued the BOX button turns red — click it again to cancel the strategy.

---

## The Pit Strategy Modal

The modal shows:

1. **Tyre compound selection** — five compounds to choose from (dry variants + INTER + WET). Each card shows the compound code, name, grip %, and cliff wear %.
2. **Front Wing Replacement** (+4.0 s) — replaces the front wing from your warehouse stock. Only available if a spare wing is in stock; greyed out with **"NO SPARE IN STOCK"** otherwise. Shows the spare's current durability %.
3. **Emergency Repairs** (+14.0 s) — a blanket repair that restores all parts currently **below 55% durability** to a random 55–60%. You cannot selectively repair individual components.
4. **Estimated stop time** — calculated and shown before you confirm.
5. **Part health overview** — current condition of all components.

> [!IMPORTANT]
> There is **no fuel option** in the pit modal. Fuel starts at 50 kg at race start and **cannot be refueled**. Manage fuel through engine mode (LEAN = 0.80× consumption).

---

## Pit Stop Timing

```
base_stop   = max(1.75, 2.4 − base_reduction)
variance    = +random(0.0 – 0.7 s)
error       = 4% base chance × error_rate_mult → +1.8 s if triggered
wing swap   = +4.0 s
repairs     = +14.0 s
```

**`base_reduction`** is determined by your **trackside facilities** — pit rig, wheel guns, and telemetry equipment all reduce the base stop time.

**Pit lane speed:** 22.2 m/s (~80 km/h). The car decelerates at 35 m/s² approaching the box and re-joins at 22.2 m/s.

---

## Repair Options in Detail

| Option | Time Cost | What it Does |
|--------|-----------|--------------|
| Tyre change (always) | Included in base stop | New compound of your choice |
| Front wing replacement | +4.0 s | Swaps to warehouse spare. Spare must exist. |
| Emergency repairs | +14.0 s | Restores sub-55% parts to 55–60%. Not selective. |

> [!NOTE]
> You **cannot** choose which individual parts to repair (e.g. brakes only). Emergency Repairs patches everything below the threshold in one go.

---

## Flag Interactions

Under **Safety Car** or **VSC**, the pit modal is accessible but **pace mode changes are locked**. The Safety Car period is generally an excellent time to pit because you lose minimal track position while the field bunches behind the SC.

---

## Improving Pit Stop Speed

Trackside facilities reduce `base_stop_reduction`:

- **Pit Rig** (track_pitrig) — increases baseline stop speed
- **Wheel Guns** (track_wheelguns) — tightens tyre change time
- **Telemetry** (track_telemetry) — reduces error rate

Upgrade these trackside nodes to shave time off every stop for both cars.
