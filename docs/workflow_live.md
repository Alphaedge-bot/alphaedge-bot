# AlphaEdge V13.0.7 – Live Workflow

## Last Updated: July 18, 2026
## Version: V13.0.7

---

## 1. OVERVIEW

AlphaEdge is a **Low Market Cap Momentum Specialist** trading bot that uses a multi-timeframe, multi-indicator approach to identify and capture momentum in micro, small, and mid-cap tokens.

**Key Features:**
- 72 agents (65 active, 7 warm standby)
- 312 strategies (278 active)
- 7 core indicators (TPS, Zones, MCDX, SMC, Volume, Macro, Volume Profile)
- 18 positions max
- TPS entry ≥82, exit ≤68
- Base currency: USDC (Stage 1) / USDC + USDT (Stage 2)

---

## 2. COMPLETE WORKFLOW DIAGRAM

```

┌─────────────────────────────────────────────────────────────────────────────┐
│                    ALPHAEDGE V13.0.7 – COMPLETE WORKFLOW                   │
└─────────────────────────────────────────────────────────────────────────────┘

STEP 1: 4H TIMEFRAME ANALYSIS (All 300+ Strategies)
┌─────────────────────────────────────────────────────────────────────────────┐
│  INPUT: 4H Price Data, Volume, On-chain, Macro, Sentiment                 │
│                                                                             │
│  📊 312 STRATEGIES APPLIED:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Category                │ Count │ Purpose                          │  │
│  │─────────────────────────│───────│──────────────────────────────────│  │
│  │ Technical TA            │ 25    │ RSI, MACD, EMA                   │  │
│  │ Price Action PA         │ 12    │ Breakout, Retest, S/R           │  │
│  │ ICT/SMC                 │ 4     │ BOS/CHoCH, OB, FVG              │  │
│  │ Wallet Whale            │ 23    │ Whale transactions, outflow     │  │
│  │ On-chain Advanced       │ 22    │ MVRV, NUPL, SOPR               │  │
│  │ Macro                   │ 20    │ Fed liquidity, DXY              │  │
│  │ Sentiment               │ 10    │ Fear & Greed, social            │  │
│  │ AI/ML                   │ 5     │ LSTM, XGBoost, Transformer      │  │
│  │ Risk Management         │ 12    │ VaR, drawdown, hedging          │  │
│  │ … (total 278 active)    │       │                                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  OUTPUT: Technical Score (0-100)                                           │
│  - ≥70 = BULLISH BIAS → Proceed to entry analysis                        │
│  - <70 = BEARISH/NEUTRAL → Skip entry                                    │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
STEP 2: TIMEFRAME SELECTION (Based on Market Cap Tier)
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Tier      │ Trend TF │ Entry TF │ ICT/SMC │ PA   │ TPS Threshold │  │
│  │───────────│──────────│──────────│─────────│──────│───────────────│  │
│  │ Micro Cap │ 1H       │ 15M      │ ✅      │ ✅   │ ≥82           │  │
│  │ Small Cap │ 4H       │ 1H       │ ✅      │ ✅   │ ≥82           │  │
│  │ Mid Cap   │ 4H       │ 1H       │ ✅      │ ✅   │ ≥82           │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  OUTPUT: Entry Timeframe Selected (1H or 15M)                              │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
STEP 3: 1H/15M ICT/SMC STRUCTURE DETECTION
┌─────────────────────────────────────────────────────────────────────────────┐
│  INPUT: 1H/15M Price Data                                                 │
│                                                                             │
│  📊 ICT/SMC COMPONENTS:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Component          │ Description                                   │  │
│  │────────────────────│───────────────────────────────────────────────│  │
│  │ BOS/CHoCH          │ Break of Structure / Change of Character     │  │
│  │ Order Blocks       │ Institutional levels (sweep + displacement)   │  │
│  │ Fair Value Gaps    │ Imbalances (with IFVG)                       │  │
│  │ OTE Zones          │ 61.8%-78.6% retracement                      │  │
│  │ Breaker Blocks     │ Failed OBs that flip direction               │  │
│  │ CISD               │ Change in State of Delivery                  │  │
│  │ Inducement (IDM)   │ Internal swing sweep                         │  │
│  │ EQH/EQL            │ Equal Highs/Lows                             │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  OUTPUT: Entry Level Identified                                             │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
STEP 4: 1H/15M PRICE ACTION CONFIRMATION
┌─────────────────────────────────────────────────────────────────────────────┐
│  INPUT: 1H/15M Candles, Volume                                            │
│                                                                             │
│  📊 PRICE ACTION COMPONENTS:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Pattern            │ Description                                   │  │
│  │────────────────────│───────────────────────────────────────────────│  │
│  │ Bullish Engulfing  │ Bullish candle fully engulfs previous bear    │  │
│  │ Hammer             │ Rejection of lower prices                    │  │
│  │ Pin Bar            │ Long wick indicates rejection                │  │
│  │ Breakout + Retest  │ Breakout retested as support                 │  │
│  │ Volume Spike       │ Volume >1.5x average                         │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  OUTPUT: Entry Confirmed (All conditions met)                              │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
STEP 5: TPS CALCULATION
┌─────────────────────────────────────────────────────────────────────────────┐
│  INPUTS: Technical, Volume, Momentum, Macro, Sentiment, On-chain, SMC     │
│                                                                             │
│  📊 TPS COMPONENTS:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Component    │ Weight │ Points │ Source                            │  │
│  │──────────────│────────│────────│───────────────────────────────────│  │
│  │ Technical    │ 30%    │ 0-30   │ RSI, MACD, EMA                    │  │
│  │ Volume       │ 25%    │ 0-25   │ Spike, ratio                      │  │
│  │ Momentum     │ 20%    │ 0-20   │ ROC, breakout                     │  │
│  │ Macro        │ 10%    │ 0-10   │ Fed, DXY                          │  │
│  │ Sentiment    │ 5%     │ 0-5    │ Fear & Greed                      │  │
│  │ On-chain     │ 5%     │ 0-5    │ Whale, outflow                    │  │
│  │ Robustness   │ 5%     │ 0-5    │ Timeframes, oracles               │  │
│  │───────────────────────────────┼───────────────────────────────────│  │
│  │ BONUS ADJUSTMENTS:               │                                   │  │
│  │ Zones (Elite) │ Bonus  │ 0-10   │ core/zone_detector.py            │  │
│  │ MCDX          │ Bonus  │ 0-10   │ core/mcdx_detector.py            │  │
│  │ SMC           │ Bonus  │ 0-10   │ core/smart_money_concepts.py     │  │
│  │ Volume Profile│ Bonus  │ 0-5    │ core/volume_profile.py          │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  OUTPUT: TPS Score (0-100)                                                 │
│  - ≥82 = STRONG BUY → Enter position                                      │
│  - 70-81 = HOLD → Maintain                                               │
│  - 50-69 = WATCH → Monitor                                               │
│  - ≤49 = SELL → Exit position                                            │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
STEP 6: ENTRY DECISION
┌─────────────────────────────────────────────────────────────────────────────┐
│  CONDITIONS:                                                              │
│  1. 4H Technical Score ≥70                                              │
│  2. 1H/15M ICT/SMC structure confirmed                                  │
│  3. 1H/15M Price Action confirmed                                       │
│  4. TPS ≥82                                                             │
│  5. Positions open <18                                                  │
│  6. Liquidity filter passed (Item 15)                                   │
│  7. Order book depth check passed (Item 19)                             │
│                                                                             │
│  ACTION: ENTRY                                                            │
│  Position Size: Dynamic Kelly (Item 26)                                   │
│  Stop Loss: Behind demand zone OR fixed % (5-8%)                          │
│  Take Profit: At supply zone OR fixed % (15-50%)                          │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
STEP 7: EXIT DECISION
┌─────────────────────────────────────────────────────────────────────────────┐
│  EXIT CONDITIONS:                                                         │
│                                                                             │
│  PRIMARY: TPS ≤68 → Sell immediately                                     │
│  SECONDARY: TPS <70 and falling → Sell early                             │
│  TERTIARY: Higher momentum token (TPS ≥82) → Replace lowest position     │
│  EMERGENCY: Drawdown >10% → Sell immediately                             │
│  ZONE: Price reaches supply zone → Take profit                           │
│  MCDX: Death Cross → Consider exit                                       │
│  SMC: Bearish BOS/CHoCH → Consider exit                                  │
│  HYSTERESIS: 3 ticks below 70 → Exit (Item 14)                           │
│                                                                             │
│  ACTION: EXIT                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
STEP 8: ROTATION
┌─────────────────────────────────────────────────────────────────────────────┐
│  ROTATION PROCESS:                                                        │
│                                                                             │
│  1. Rank all tracked tokens by TPS score                                  │
│  2. Identify lowest TPS positions (TPS <68)                               │
│  3. Apply hysteresis buffer (3 ticks below 70)                            │
│  4. Sell lowest TPS positions                                             │
│  5. Find highest TPS tokens not in positions (TPS ≥82)                    │
│  6. Check liquidity filter and order book depth                           │
│  7. Enter highest TPS tokens                                              │
│  8. Repeat every 60 seconds                                              │
│                                                                             │
│  GOAL: Always hold the top 18 tokens by TPS score                         │
└─────────────────────────────────────────────────────────────────────────────┘

```

---

## 3. INDICATORS INTEGRATED

| Indicator | Source | Purpose | TPS Adjustment |
|-----------|--------|---------|----------------|
| **Zones (ICT/SMC)** | `core/zone_detector.py` | Order blocks, FVG | +10 (Elite) |
| **MCDX** | `core/mcdx_detector.py` | Market chip distribution | +5 (GC), +8 (BC) |
| **SMC (LuxAlgo)** | `core/smart_money_concepts.py` | BOS/CHoCH, OB, FVG | +6 (BOS), +4 (CHoCH) |
| **SMC (Validated)** | `core/smart_money_concepts.py` | Breaker, IFVG, OTE, CISD | +8 (OB), +6 (Breaker) |
| **Volume Profile** | `core/volume_profile.py` | Multi-TF POC, VAH, VAL | +5 |
| **Technical** | `agent_06_technical.py` | RSI, MACD, EMA | 0-30 |
| **Volume** | `agent_06_technical.py` | Spike, ratio | 0-25 |
| **Momentum** | `agent_69_momentum_rotator.py` | ROC, breakout | 0-20 |
| **Macro** | `agent_03_macro_analyst.py` | Fed, DXY | 0-10 |

---

## 4. KEY AGENTS AND ROLES

| Agent | Role |
|-------|------|
| **Agent_00 (CEO)** | Strategic direction, approvals, conflict resolution |
| **Agent_03 (Macro Analyst)** | Fed liquidity, DXY, market regime |
| **Agent_06 (Technical)** | TA, PA, ICT/SMC, zone detection, Volume Profile |
| **Agent_18 (Risk Guardian)** | Risk management, SL/TP, circuit breakers, Order Book Depth |
| **Agent_30 (Self-Evolving)** | Code improvement proposals, workflow updates, Parallel Audit |
| **Agent_56 (Optimizer)** | Parameter optimization, Bayesian optimization |
| **Agent_62 (Position Sizer)** | Dynamic Kelly, Fractional Kelly, Micro-cap sizing |
| **Agent_63 (Profit Taking)** | Order execution, exits, gold swaps, Liquidity Filter |
| **Agent_69 (Momentum Rotator)** | TPS calculation, token rotation, Hysteresis Buffer |
| **Agent_72 (Command Interface)** | Telegram/web dashboard, user commands, Scam Warning |
| **Agent_73 (Narrative Catalyst)** | Early signal detection via LLM |

---

## 5. POSITION MANAGEMENT

| Rule | Value |
|------|-------|
| Max Positions | 18 |
| Position Size (Micro) | 2-4% (Dynamic Kelly) |
| Position Size (Small) | 3-5% (Dynamic Kelly) |
| Position Size (Mid) | 4-6% (Dynamic Kelly) |
| Rotation Frequency | Every 60 seconds |
| Micro Cap Multiplier | 1.15x |
| Hysteresis Buffer | 3 ticks below 70 before exit |
| Liquidity Filter | Min 24h volume $500K |

---

## 6. TPS THRESHOLDS

| Score | Action |
|-------|--------|
| ≥82 | STRONG BUY – Enter position |
| 70-81 | HOLD – Maintain position |
| 50-69 | WATCH – Monitor |
| ≤49 | SELL – Exit position |

---

## 7. SCAM WARNING

AlphaEdge **NEVER** asks for investment, runs paid ads, or solicits public funds.

If someone asks you for money using the AlphaEdge name:
- ❌ They are scammers
- ❌ Do not send any money
- ❌ Report them immediately

Use `/scam_warning` to display the warning or `/scam_report` to report an attempt.

---

## 8. CHANGE LOG

| Date | Change | Agent |
|------|--------|-------|
| July 18, 2026 | Added Volume Profile | Agent_06 |
| July 18, 2026 | Added Scam Warning | Agent_50, Agent_72 |
| July 18, 2026 | Added Marketing Enhancements | Agent_50 |
| July 18, 2026 | Added C++/Rust Extensions | Agent_30 |
| July 18, 2026 | Added Redis Message Bus | Agent_30 |
| July 18, 2026 | Added Parallel Execution Audit | Agent_30 |
| July 18, 2026 | Added FPGA Reassessment | Agent_30 |
| July 18, 2026 | Updated to V13.0.7 | Agent_30 |
| July 14, 2026 | Added Smart Money Concepts validation layer | Agent_30 |
| July 14, 2026 | Added MCDX Plus integration | Agent_56 |
| July 13, 2026 | Added ICT/SMC Zone Detection | Agent_06 |
| July 12, 2026 | Updated TPS thresholds (82/68) | Agent_56 |

---

*This document is auto-updated by AlphaEdge AI agents. Last update: July 18, 2026*
`
