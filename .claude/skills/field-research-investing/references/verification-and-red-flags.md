# Physical verification and red flags

## Contents
1. Counting as an experiment
2. Choosing what to count
3. Conversion factors
4. Sampling plan and observers
5. Computing and reconciling (field_math.py)
6. Asking the company, and reading the response
7. Publishing or acting on a negative finding
8. Accounting and reporting red flags
9. Behavioral and market red flags
10. When the signal points the other way

---

## 1. Counting as an experiment

In science, a claim is tested by repeating a physical measurement. Stock research almost never does this; reported numbers are accepted and argued over on paper. Counting physical units (trucks, containers, cartons, shifts) is a repeatable experiment that anyone can check, and it can reveal that reported revenue or volume is impossible. It is tedious, so use it where a discrepancy is suspected or a decision depends on volume. Owners who never count what they hold tend to sell it too cheaply to someone who did count.

Best targets: a company with one main plant and one warehouse, a product that leaves in standard loads, and public vantage points.

## 2. Choosing what to count

| Unit | Link to revenue | Watch out for |
|---|---|---|
| Outbound loaded trucks or containers | Units per load × price | Partial loads; returns; shipments between own sites |
| Packaging or labels from an outside supplier | One per unit sold | Supplier serving other customers; stockpiling |
| Rail cars, vessels, barges | Tonnage × price | Inventory transfers |
| Staff shifts, cars in staff lot | Labor hours × productivity | Maintenance shutdowns; overtime for other reasons |
| Inbound raw material deliveries | Input per unit | Inventory building |
| Warehouse fill level (seen from outside, over weeks) | Direction of inventory | Seasonality |

## 3. Conversion factors

- **Units per load:** product specifications (unit weight and dimensions), standard pallet configurations, the legal maximum load for the truck type (public road-weight rules; weigh-station limits). Use the maximum for an upper bound.
- **Price per unit:** a published price list, distributor pricing, or an ordinary quote requested as a genuine inquiry. Adjust for discounts and mix.
- **Operating days:** working days in the period; seasonality from past reports or industry data.

## 4. Sampling plan and observers

- Cover representative days and all hours of dispatch (or know the shipping hours).
- Log each event with date, time, vehicle type, apparent load, and direction; a photo from a public place where appropriate.
- If you cannot stay for the whole period, hire reliable observers (for example, students vetted through someone you trust), pay them yourself, brief them on the rules (public places only, no conversations under false pretenses, no photographs of people), and spot-check their logs. Weekly checks of warehouse fill (from outside) show whether inventory is building or draining.
- Keep originals of all logs; you may need to show them.

## 5. Computing and reconciling (field_math.py)

`python3 scripts/field_math.py unitcount --counts 31,28,35,30,33 --units-per-load 1200 --price 2.10 --period-days 63 --reported 9500000 [--load-factor 0.85] [--other-revenue 0]`

It reports average loads per observed day with a confidence range, estimated period revenue at the given load factor and at full load (an upper bound), the reported figure, and the gap in money and percent. Interpretation:
- Reported revenue **above the full-load upper bound** for the observed volume is a serious red flag, unless revenue comes from other sites, other channels or non-shipment sources: list and check these before concluding.
- Small gaps can come from mix, timing (shipments versus recognition), price changes or sampling error; widen the sample before drawing conclusions.
- Always state assumptions (load factor, price, days) and test sensitivity.

## 6. Asking the company, and reading the response

1. Ask the finance chief a specific question by phone first; if brushed off, put a polite, specific written question to the finance chief with a copy to the chief executive.
2. Note how competitors react when asked about the company in general: a pointed silence, knowing shrugs or meaningful pauses are themselves information.
3. Read the response:

| Healthy response | Warning response |
|---|---|
| Addresses the physical question directly (other plants, contract manufacturers, timing) | Bureaucratic generalities, complex accounting explanations that do not touch the volume question |
| Offers a visit or data that can be checked | "Focus on our guidance" |
| Corrects a factual error you made | Attacks spelling or minor errors while ignoring the core finding |
| Engages with the evidence | Lines up consultants' industry reports and accounting-compliance opinions instead of answering |
| | Pressure on the questioner: complaints to their employer, legal letters, demands to stop covering the company |
| | Friendly analysts at firms with banking ties rushing to defend the company without addressing the evidence |

A large physical gap plus a deflecting response is one of the strongest negative patterns. Pressure on an analyst to stop coverage is a lead worth following immediately; ask analyst contacts (discreetly) about such cases.

## 7. Publishing or acting on a negative finding

- Only act on facts you can document; keep the logs, photographs and correspondence.
- Before publishing anything, have it reviewed by a lawyer: stick to verifiable facts and the method used, avoid accusations of motive, disclose your own position, and observe applicable rules on research and trading around publication. A report that simply says the reported numbers cannot be reconciled with observed shipments, shows the data and offers the logs is far safer than one that alleges fraud.
- Expect counter-attacks, a falling stock that the company blames on "rumors", and pressure from people whose interests depend on the company. Regulators may ask for your notes; cooperate.
- Shorting carries unlimited loss potential and squeeze risk; size accordingly (decision-and-risk.md).

## 8. Accounting and reporting red flags

- Revenue growing faster than physical shipments, or faster than cash collections; receivables and inventory rising faster than sales.
- Shipments to distributors booked as sales beyond what they can sell (channel stuffing), especially just before insiders exercise options and sell.
- Accounting items presented as sales; "non-recurring" charges that recur.
- Backdated option grants, revealed in obscure notes.
- Guidance far above what observable capacity or demand can support.
- Auditor changes, late filings, restatements, chief financial officer leaving "for health reasons" or "to pursue other interests".
- Debt with tight coverage covenants (minimum revenue or cash-flow ratios) on a company whose orders are lumpy: one delayed order can breach them.
- A company that needs to issue new shares soon after a period of strong claims.

## 9. Behavioral and market red flags

- Management denying rumors nobody had heard of; suing short sellers; publicly disputing analysts.
- Heavy promotion; executives more visible in society pages than in customers' offices.
- A leader surrounded by public-relations staff; engineers or staff near-unanimously contemptuous of leadership.
- Customers ecstatic about a vendor that must outspend everyone to stay at the top of a non-growing niche.
- Pressure to decide quickly on a single channel of information, with discouragement from checking in person.
- Locals near a remote operation who laugh, refuse to talk, or hang up when asked about it (events-and-crises.md §3).

## 10. When the signal points the other way

- An analyst who was wrong all the way down finally capitulates: if the company survives the institutional selling that follows, it may be worth researching as a long.
- A company whose reported numbers are *understated* relative to physical activity (conservative recognition, capacity hidden in overflow vendors) can be a quiet long.
- Reconcile both ways: the same counting method that exposes inflated revenue can confirm a surge before it is reported.
