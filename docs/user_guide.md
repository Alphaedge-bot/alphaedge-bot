# AlphaEdge V13.0.5 – User Guide

## Welcome to AlphaEdge

AlphaEdge is a **Low Market Cap Momentum Specialist** trading bot designed for micro, small, and mid-cap tokens. This guide will help you understand how to operate the bot and make the most of its features.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Bot Architecture](#bot-architecture)
3. [Core Principles](#core-principles)
4. [Trading Strategy](#trading-strategy)
5. [Wallet Structure](#wallet-structure)
6. [Commands](#commands)
7. [Gold Swap Strategy](#gold-swap-strategy)
8. [Risk Management](#risk-management)
9. [Monitoring & Reporting](#monitoring--reporting)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- **Hardware**: Stage 1 (DDR4) or Stage 2 (FPGA Dual Node)
- **Network**: 500Mbps wired connection
- **Power**: UPS with 5G wireless backup
- **Wallet**: USDC (Stage 1) or USDC + USDT (Stage 2)

### Quick Start

1. Clone the repository:
```

git clone https://github.com/Alphaedge-bot/alphaedge-bot.git
cd alphaedge-bot

```

2. Install dependencies:
```

pip install -r requirements.txt

```

3. Configure wallets in `config/config.yaml`

4. Start the bot:
```

python main.py

```

---

## Bot Architecture

### Agents (72 Agents)

The bot uses 72 specialized agents organized into 8 layers:

| Layer | Agents | Purpose |
|-------|--------|---------|
| Executive | 3 | Strategic direction, coordination |
| Data Intelligence | 13 | Market data, on-chain, sentiment |
| Debate Decision | 8 | Entry/exit decisions, risk management |
| Execution Optimization | 13 | Order execution, MEV protection |
| Robustness & Resilience | 14 | Failover, healing, monitoring |
| Support & Operational | 21 | Marketing, auditing, commands |

### Key Agents

- **Agent 00 (CEO)**: Strategic direction and approvals
- **Agent 18 (Risk Guardian)**: Risk management, stop losses
- **Agent 63 (Profit Taking)**: Gold swap, order execution
- **Agent 69 (Momentum Rotator)**: Token selection via TPS
- **Agent 72 (Command Interface)**: Telegram/web dashboard

---

## Core Principles

1. **Momentum-only breakout strategy**
2. **Hold ONLY highest momentum tokens** (by ROC velocity)
3. **Post only after breakout** (never during range)
4. **Price action FIRST** – Indicators confirm only
5. **Upgrade only** – Never downgrade
6. **NO lending protocols** – NO yield generation
7. **Fed Liquidity** = Primary macro risk toggle
8. **DXY HIGH** = Stablecoins (not Crypto)

---

## Trading Strategy

### Trading Universe

| Cap Tier | Range | Max Positions |
|----------|-------|---------------|
| Micro | <$50M | 2-6 |
| Small | $50M-200M | 4-10 |
| Mid | $200M-1B | 4-12 |

**Excluded:**
- Large cap (>$1B)
- Lending tokens (AAVE, COMP, MKR, RDNT)
- Gambling tokens

### Ticker Performance Score (TPS)

TPS evaluates each asset for entry/exit decisions (0-100 scale):

| Score Range | Action |
|-------------|--------|
| ≥82 | STRONG BUY – Enter position |
| 70-81 | MAINTAIN – Hold position |
| 50-69 | WATCH – Monitor |
| ≤49 | SELL/EXIT – Exit position |

**TPS Components:**
- Technical: 30 points (RSI, MACD, EMA)
- Volume: 25 points (Spike, Ratio)
- Momentum: 20 points (ROC, Breakout)
- Macro: 10 points (Fed, DXY)
- Sentiment: 5 points
- On-chain: 5 points
- Robustness: 5 points

---

## Wallet Structure

### Wallet 1 – Trading Capital
- **Purpose**: 100% trading capital
- **Balance**: USDC (Stage 1) / USDC+USDT (Stage 2)
- **Access**: Bot FULL, User VIEW ONLY
- **Limit**: $25,000 (Stage 1 hard cap)

### Wallet 2 – Operations
- **Purpose**: Gas fees + API costs
- **Balance**: SOL (1.0), ETH (0.05), BNB (0.5)
- **Access**: Bot AUTO-PAY, User VIEW + APPROVE

### Wallet 3 – User Profit
- **Purpose**: User profit + Stage 2 savings
- **Balance**: USDC
- **Access**: Bot DEPOSIT ONLY, User FULL

---

## Commands

### Gold Swap Commands

| Command | Description |
|---------|-------------|
| `/swap_gold 1000` | Swap USDT to PAXG |
| `/swap_gold 1000 --paxg` | Force swap to PAXG |
| `/swap_gold 1000 --xaut` | Force swap to XAUT |
| `/gold_status` | Check gold holdings |
| `/gold_price` | Check PAXG price |
| `/swap_stable` | Swap gold back to stable |

### General Commands

| Command | Description |
|---------|-------------|
| `/status` | Bot status |
| `/balance` | Wallet balances |
| `/positions` | Current positions |
| `/performance` | Bot performance |
| `/health` | System health |

---

## Gold Swap Strategy

### PAXG (Primary) + XAUT (Fallback)

The bot automatically swaps to gold when stablecoins depeg:

```

Depeg Detected (>1%)
↓
Check PAXG Availability
↓
┌────┴────┐
↓         ↓
PAXG OK    PAXG Failed
↓         ↓
→ PAXG    → XAUT (Fallback)

```

### Best Platforms

| Platform | Chain | Fee | Slippage | Recommendation |
|----------|-------|-----|----------|----------------|
| Jupiter | Solana | 0.2% | 0.1% | ✅ BEST |
| 1inch | Arbitrum | 0.1% | 0.1% | ✅ BEST |
| PancakeSwap | BSC | 0.25% | 0.3% | ✅ GOOD |
| Uniswap | Base | 0.3% | 0.2% | ✅ GOOD |

---

## Risk Management

### Stop Loss (By Cap Tier)

| Tier | Fixed % | Trailing % |
|------|---------|------------|
| Micro | 4% | 3-4% |
| Small | 5% | 4-5% |
| Mid | 7% | 6-7% |
| Large | 8% | 8% |

### Take Profit Targets

| Tier | Target | Take % |
|------|--------|--------|
| 1 | +15% | 25% |
| 2 | +25% | 25% |
| 3 | +50% | 25% |
| 4 | +100% | 25% |

### Circuit Breakers

| Condition | Action |
|-----------|--------|
| 3 consecutive losses | Pause 1 hour |
| 10% daily drawdown | Reduce size 50% |
| 15% weekly drawdown | Switch to stablecoins |
| 20% monthly drawdown | Emergency shutdown |

---

## Monitoring & Reporting

### Bot Performance Grade (BPG)

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 90-100% | Exceptional |
| B | 75-89% | Strong |
| C | 60-74% | Average |
| D | 45-54% | Needs Improvement |
| F | 0-44% | Critical Issues |

### Daily Reports

- **Public Digest**: Educational content (12:00 UTC)
- **Private Digest**: Full performance details
- **Risk Report**: Daily risk metrics
- **Audit Log**: Immutable transaction log

---

## Troubleshooting

### Common Issues

**Issue**: Bot not starting
```

Solution: Check config files in /config directory
Ensure all YAML files are valid

```

**Issue**: RPC connection failed
```

Solution: Check RPC endpoints in config/rpc_config.yaml
Bot will auto-failover to backup RPCs

```

**Issue**: Gold swap failing
```

Solution: Check PAXG/XAUT liquidity
Bot will attempt fallback to XAUT
Check gas reserves in wallet 2

```

**Issue**: High slippage
```

Solution: Reduce order size (split into multiple orders)
Bot auto-splits orders >$5,000
Check liquidity on chosen platform

```

### Emergency Procedures

1. **Manual override**: Use `/force_failover` to switch RPC
2. **Circuit breaker**: Auto-triggered at 3 losses
3. **Black swan**: Auto-switch to stablecoins
4. **Manual gold swap**: Use `/swap_gold` commands

---

## Support

- **GitHub**: https://github.com/Alphaedge-bot/alphaedge-bot
- **Telegram**: @AlphaEdgeBot
- **Documentation**: https://github.com/Alphaedge-bot/alphaedge-bot/docs

---

## Version Information

- **Current Version**: V13.0.5
- **Status**: Production Ready
- **Release Date**: July 7, 2026
- **Rating**: 13/13 (Theoretical Maximum)

---

*AlphaEdge V13.0.5 – Built for performance. Designed for reliability.*
```
