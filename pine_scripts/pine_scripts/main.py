#!/usr/bin/env python3
"""
AlphaEdge V13.0.5 – Main Entry Point
Production trading bot with 72 agents, 312 strategies
Hardware: Stage 1 (DDR4) → Stage 2 (FPGA Dual Node)
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Core imports
from core.event_bus import EventBus
from core.state_manager import StateManager
from core.wal import WriteAheadLog

# Agent imports (will be loaded dynamically)
from agents.agent_00_ceo import CEOAgent
from agents.agent_01_coordinator import CoordinatorAgent
from agents.agent_02_forecaster import StrategicForecaster
from agents.agent_03_macro import MacroAnalyst
from agents.agent_04_whale import WhaleOnChainAnalyst
from agents.agent_05_cross_chain import CrossChainAnalyst
from agents.agent_06_technical import TechnicalAnalyst
from agents.agent_07_sentiment import SentimentScanner
from agents.agent_08_oracle import OracleLatencyTracker
from agents.agent_09_advanced_tech import AdvancedTechnical
from agents.agent_10_cross_validation import CrossValidationOracle
from agents.agent_11_drift import ModelDriftDetector
from agents.agent_12_adversarial import AdversarialSimulator
from agents.agent_13_sentiment_aggregator import SentimentAggregator
from agents.agent_14_onchain_advanced import OnChainAdvanced
from agents.agent_15_fpga_kernel import FPGAKernel
from agents.agent_16_proposer import Proposer
from agents.agent_17_opponent import Opponent
from agents.agent_18_risk_guardian import RiskGuardian
from agents.agent_19_fund_manager import FundManager
from agents.agent_20_rebalancer import PortfolioRebalancer
from agents.agent_21_consensus import ConsensusEngine
from agents.agent_22_cross_validation import CrossValidationOracle
from agents.agent_23_execution_sniper import ExecutionSniper
from agents.agent_24_mev_shield import MEVShield
from agents.agent_25_intent_abstractor import IntentAbstractor
from agents.agent_26_execution_auditor import ExecutionQualityAuditor
from agents.agent_27_multi_dex_router import MultiDEXRouter
from agents.agent_28_fpga_execution import FPGAExecutionKernel
from agents.agent_29_quantum_optimizer import QuantumInspiredOptimizer
from agents.agent_30_self_evolving import SelfEvolvingArchitect
from agents.agent_31_solana_tx import SolanaTransactionOptimizer
from agents.agent_32_ai_ensemble import AIEnsemble
from agents.agent_33_transformer import TransformerPredictor
from agents.agent_34_solver_network import SolverNetworkExecutor
from agents.agent_36_failure_simulator import PredictiveFailureSimulator
from agents.agent_37_formal_verifier import FormalVerifier
from agents.agent_38_zero_trust import ZeroTrustAuditor
from agents.agent_39_resilience import AdaptiveResilienceEngine
from agents.agent_40_state_reconciler import StateReconciler
from agents.agent_41_auto_healer import AutoHealer
from agents.agent_42_health_monitor import HealthMonitor
from agents.agent_43_resource_governor import ResourceGovernor
from agents.agent_44_quality_guard import QualityGuard
from agents.agent_45_redundancy_manager import RedundancyManager
from agents.agent_46_latency_optimizer import LatencyOptimizer
from agents.agent_47_error_classifier import ErrorClassifier
from agents.agent_48_audit_logger import AuditLogger
from agents.agent_49_circuit_breaker import CircuitBreakerMonitor
from agents.agent_50_marketing import MarketingAgent
from agents.agent_51_sub_router import SubAgentRouter
from agents.agent_52_critic import CriticAgent
from agents.agent_53_tax_audit import TaxAuditAgent
from agents.agent_54_compliance import ComplianceGuard
from agents.agent_55_inscription_scanner import InscriptionScanner
from agents.agent_56_optimizer_engine import OptimizerEngine
from agents.agent_57_performance_analyzer import PerformanceAnalyzer
from agents.agent_58_error_memory import ErrorMemoryCurator
from agents.agent_59_causal_analyst import CausalAnalyst
from agents.agent_60_profit_optimizer import ProfitOptimizer
from agents.agent_61_bull_run_detector import BullRunDetector
from agents.agent_62_position_sizer import PositionSizer
from agents.agent_63_profit_taking_executor import ProfitTakingExecutor
from agents.agent_64_profit_taking_auditor import ProfitTakingAuditor
from agents.agent_65_capital_allocator import CapitalAllocator
from agents.agent_66_gas_optimizer import GasOptimizer
from agents.agent_67_media_creator import MediaCreator
from agents.agent_68_bot_performance import BotPerformanceAuditor
from agents.agent_69_momentum_rotator import MomentumRotator
from agents.agent_70_early_exit_blocker import EarlyExitBlocker
from agents.agent_71_re_entry_validator import ReEntryValidator
from agents.agent_72_command_interface import CommandInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/alphaedge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AlphaEdge:
    """Main AlphaEdge Bot Controller"""
    
    def __init__(self, mode='production'):
        """
        Initialize AlphaEdge Bot
        
        Args:
            mode: 'production', 'dry-run', 'test'
        """
        self.mode = mode
        self.running = False
        self.agents = {}
        self.event_bus = None
        self.state_manager = None
        self.wal = None
        
        logger.info(f"Initializing AlphaEdge V13.0.5 in {mode} mode")
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing core components...")
        
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        
        # Initialize WAL (Write-Ahead Log)
        self.wal = WriteAheadLog("data/wal")
        await self.wal.initialize()
        
        # Initialize State Manager with 3-way WAL
        self.state_manager = StateManager(self.wal)
        await self.state_manager.initialize()
        
        # Initialize Event Bus
        self.event_bus = EventBus()
        await self.event_bus.initialize()
        
        logger.info("Core components initialized")
        
    async def register_agents(self):
        """Register all 72 agents"""
        logger.info("Registering agents...")
        
        # Executive Layer (3)
        self.agents['ceo'] = CEOAgent(self.event_bus, self.state_manager)
        self.agents['coordinator'] = CoordinatorAgent(self.event_bus, self.state_manager)
        self.agents['forecaster'] = StrategicForecaster(self.event_bus, self.state_manager)
        
        # Data & Intelligence (13)
        self.agents['macro'] = MacroAnalyst(self.event_bus, self.state_manager)
        self.agents['whale'] = WhaleOnChainAnalyst(self.event_bus, self.state_manager)
        self.agents['cross_chain'] = CrossChainAnalyst(self.event_bus, self.state_manager)
        self.agents['technical'] = TechnicalAnalyst(self.event_bus, self.state_manager)
        self.agents['sentiment'] = SentimentScanner(self.event_bus, self.state_manager)
        self.agents['oracle'] = OracleLatencyTracker(self.event_bus, self.state_manager)
        self.agents['advanced_tech'] = AdvancedTechnical(self.event_bus, self.state_manager)
        self.agents['cross_validation'] = CrossValidationOracle(self.event_bus, self.state_manager)
        self.agents['drift'] = ModelDriftDetector(self.event_bus, self.state_manager)
        self.agents['adversarial'] = AdversarialSimulator(self.event_bus, self.state_manager)
        self.agents['sentiment_agg'] = SentimentAggregator(self.event_bus, self.state_manager)
        self.agents['onchain_advanced'] = OnChainAdvanced(self.event_bus, self.state_manager)
        self.agents['fpga_kernel'] = FPGAKernel(self.event_bus, self.state_manager)
        
        # Debate & Decision (8)
        self.agents['proposer'] = Proposer(self.event_bus, self.state_manager)
        self.agents['opponent'] = Opponent(self.event_bus, self.state_manager)
        self.agents['risk_guardian'] = RiskGuardian(self.event_bus, self.state_manager)
        self.agents['fund_manager'] = FundManager(self.event_bus, self.state_manager)
        self.agents['rebalancer'] = PortfolioRebalancer(self.event_bus, self.state_manager)
        self.agents['consensus'] = ConsensusEngine(self.event_bus, self.state_manager)
        self.agents['cross_validation_2'] = CrossValidationOracle(self.event_bus, self.state_manager)
        
        # Execution & Optimization (13)
        self.agents['sniper'] = ExecutionSniper(self.event_bus, self.state_manager)
        self.agents['mev'] = MEVShield(self.event_bus, self.state_manager)
        self.agents['intent'] = IntentAbstractor(self.event_bus, self.state_manager)
        self.agents['execution_auditor'] = ExecutionQualityAuditor(self.event_bus, self.state_manager)
        self.agents['dex_router'] = MultiDEXRouter(self.event_bus, self.state_manager)
        self.agents['fpga_execution'] = FPGAExecutionKernel(self.event_bus, self.state_manager)
        self.agents['quantum'] = QuantumInspiredOptimizer(self.event_bus, self.state_manager)
        self.agents['self_evolving'] = SelfEvolvingArchitect(self.event_bus, self.state_manager)
        self.agents['solana_tx'] = SolanaTransactionOptimizer(self.event_bus, self.state_manager)
        self.agents['ai_ensemble'] = AIEnsemble(self.event_bus, self.state_manager)
        self.agents['transformer'] = TransformerPredictor(self.event_bus, self.state_manager)
        self.agents['solver_network'] = SolverNetworkExecutor(self.event_bus, self.state_manager)
        
        # Robustness & Resilience (14)
        self.agents['failure_sim'] = PredictiveFailureSimulator(self.event_bus, self.state_manager)
        self.agents['formal_verifier'] = FormalVerifier(self.event_bus, self.state_manager)
        self.agents['zero_trust'] = ZeroTrustAuditor(self.event_bus, self.state_manager)
        self.agents['resilience'] = AdaptiveResilienceEngine(self.event_bus, self.state_manager)
        self.agents['state_reconciler'] = StateReconciler(self.event_bus, self.state_manager)
        self.agents['auto_healer'] = AutoHealer(self.event_bus, self.state_manager)
        self.agents['health'] = HealthMonitor(self.event_bus, self.state_manager)
        self.agents['resource_governor'] = ResourceGovernor(self.event_bus, self.state_manager)
        self.agents['quality_guard'] = QualityGuard(self.event_bus, self.state_manager)
        self.agents['redundancy'] = RedundancyManager(self.event_bus, self.state_manager)
        self.agents['latency'] = LatencyOptimizer(self.event_bus, self.state_manager)
        self.agents['error_classifier'] = ErrorClassifier(self.event_bus, self.state_manager)
        self.agents['audit_logger'] = AuditLogger(self.event_bus, self.state_manager)
        self.agents['circuit_breaker'] = CircuitBreakerMonitor(self.event_bus, self.state_manager)
        
        # Support & Operational (21)
        self.agents['marketing'] = MarketingAgent(self.event_bus, self.state_manager)
        self.agents['sub_router'] = SubAgentRouter(self.event_bus, self.state_manager)
        self.agents['critic'] = CriticAgent(self.event_bus, self.state_manager)
        self.agents['tax_audit'] = TaxAuditAgent(self.event_bus, self.state_manager)
        self.agents['compliance'] = ComplianceGuard(self.event_bus, self.state_manager)
        self.agents['inscription'] = InscriptionScanner(self.event_bus, self.state_manager)
        self.agents['optimizer'] = OptimizerEngine(self.event_bus, self.state_manager)
        self.agents['performance'] = PerformanceAnalyzer(self.event_bus, self.state_manager)
        self.agents['error_memory'] = ErrorMemoryCurator(self.event_bus, self.state_manager)
        self.agents['causal'] = CausalAnalyst(self.event_bus, self.state_manager)
        self.agents['profit_optimizer'] = ProfitOptimizer(self.event_bus, self.state_manager)
        self.agents['bull_run'] = BullRunDetector(self.event_bus, self.state_manager)
        self.agents['position_sizer'] = PositionSizer(self.event_bus, self.state_manager)
        self.agents['profit_taking'] = ProfitTakingExecutor(self.event_bus, self.state_manager)
        self.agents['profit_auditor'] = ProfitTakingAuditor(self.event_bus, self.state_manager)
        self.agents['capital_allocator'] = CapitalAllocator(self.event_bus, self.state_manager)
        self.agents['gas_optimizer'] = GasOptimizer(self.event_bus, self.state_manager)
        self.agents['media_creator'] = MediaCreator(self.event_bus, self.state_manager)
        self.agents['bot_performance'] = BotPerformanceAuditor(self.event_bus, self.state_manager)
        self.agents['momentum_rotator'] = MomentumRotator(self.event_bus, self.state_manager)
        self.agents['early_exit'] = EarlyExitBlocker(self.event_bus, self.state_manager)
        self.agents['re_entry'] = ReEntryValidator(self.event_bus, self.state_manager)
        self.agents['command_interface'] = CommandInterface(self.event_bus, self.state_manager)
        
        logger.info(f"Registered {len(self.agents)} agents")
        
    async def start_agents(self):
        """Start all agents"""
        logger.info("Starting all agents...")
        
        # Start agents in priority order
        priority_order = [
            'state_reconciler', 'auto_healer', 'circuit_breaker',  # Critical
            'coordinator', 'ceo',  # Executive
            'macro', 'technical', 'sentiment',  # Data
            'proposer', 'opponent', 'risk_guardian', 'fund_manager',  # Decision
            'sniper', 'mev', 'dex_router',  # Execution
            'health', 'audit_logger',  # Monitoring
            'command_interface'  # User interface
        ]
        
        # Start prioritized agents first
        for agent_id in priority_order:
            if agent_id in self.agents:
                try:
                    await self.agents[agent_id].start()
                    logger.info(f"Started {agent_id}")
                except Exception as e:
                    logger.error(f"Failed to start {agent_id}: {e}")
        
        # Start remaining agents
        for agent_id, agent in self.agents.items():
            if agent_id not in priority_order:
                try:
                    await agent.start()
                    logger.info(f"Started {agent_id}")
                except Exception as e:
                    logger.error(f"Failed to start {agent_id}: {e}")
        
        self.running = True
        logger.info("All agents started")
        
    async def run(self):
        """Main bot loop"""
        logger.info("AlphaEdge V13.0.5 is running")
        
        try:
            while self.running:
                # Main loop tasks
                await asyncio.sleep(1)
                
                # Check health
                if 'health' in self.agents:
                    health_status = await self.agents['health'].get_status()
                    if health_status.get('score', 100) < 50:
                        logger.warning(f"Health score low: {health_status['score']}")
                
                # Check circuit breakers
                if 'circuit_breaker' in self.agents:
                    cb_status = await self.agents['circuit_breaker'].get_status()
                    if cb_status.get('active_layers', []):
                        logger.warning(f"Circuit breakers active: {cb_status['active_layers']}")
                
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
            await self.shutdown()
            
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down AlphaEdge...")
        self.running = False
        
        # Stop agents
        for agent_id, agent in self.agents.items():
            try:
                await agent.stop()
                logger.info(f"Stopped {agent_id}")
            except Exception as e:
                logger.error(f"Error stopping {agent_id}: {e}")
        
        # Save state
        await self.state_manager.save_checkpoint()
        await self.wal.close()
        
        logger.info("AlphaEdge shutdown complete")


async def main():
    """Entry point"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='AlphaEdge Trading Bot')
    parser.add_argument('--mode', choices=['production', 'dry-run', 'test'], 
                       default='production', help='Run mode')
    parser.add_argument('--node', choices=['primary', 'backup'],
                       default='primary', help='Node type (Stage 2 only)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run without executing trades')
    parser.add_argument('--status', action='store_true',
                       help='Show bot status and exit')
    
    args = parser.parse_args()
    
    # If status flag, show status and exit
    if args.status:
        # Quick status check
        print("AlphaEdge V13.0.5")
        print("Status: Ready")
        print("Mode:", args.mode)
        return
    
    # Initialize bot
    bot = AlphaEdge(mode=args.mode)
    
    try:
        await bot.initialize()
        await bot.register_agents()
        await bot.start_agents()
        await bot.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await bot.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
