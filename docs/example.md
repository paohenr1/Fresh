# A fictional projection year

Run commands from the repository root.

## Walk through a fictional year

The provided example's first year is **2026**, t=0. The client retires in 2026;
the spouse continues working until 2029. Both plans are active.

| Step | Nominal CAD, displayed to cents |
|---|---:|
| Opening household savings | 495,000.00 |
| Spouse contributions, before growth (1,000 + 5,000 + 3,000) | 9,000.00 |
| Gross target (60,000 + 50,000) | 110,000.00 |
| Working spouse's employment income | 50,000.00 |
| Client's fixed pension | 18,000.00 |
| Client CPP: 18,092 × 200/365 | 9,913.42 |
| Client OAS: 8,908 × 200/365 | 4,881.10 |
| Beginning-of-year draw needed | 27,205.48 |
| Investment return after the draw | 22,285.53 |
| Closing savings | 499,080.05 |
| Unmet target | 0.00 |

There are 200 calendar days from June 15 through December 31, inclusive.
Available Cash is 36,000 after spouse contributions. The 27,205.479452 draw
is allocated pro rata: client has 25,000 of 36,000 and spouse has 11,000.
Remaining client assets earn 4%; remaining spouse assets earn 6%. Cash funds
the entire draw; RRSP and TFSA are untouched except for contributions and growth.

Reconciliation at full precision is
495,000 + 9,000 − 27,205.479452054795 + 22,285.52511415525
= 499,080.0456621004. Display rounding can produce a one-cent discrepancy if
you add the individually rounded table amounts. Today's-dollar values equal
nominal values in this first year. In 2027 spouse RRSP contribution becomes
5,000 × 1.025 = 5,125; its purchasing power is 5,125 / 1.02 = 5,024.5098.

The example ends in 2033 with nominal savings 512,320.5542, or 446,005.8731
in 2026 purchasing power. All 8 projected retirement years are funded.


[Back to the README](../README.md).
