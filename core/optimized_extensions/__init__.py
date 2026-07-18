# core/optimized_extensions/__init__.py
# AlphaEdge V13.0.7 – C++/Rust Extensions Framework
# Item 22: C++/Rust Extensions

"""
C++/Rust Extensions Framework

This module provides a framework for C++/Rust extensions to accelerate
computationally heavy operations in AlphaEdge.

Planned extensions:
- Matrix calculations (312 strategies)
- ICT/SMC pattern detection
- Volume Profile calculations
- MCDX calculations

Usage:
    from core.optimized_extensions import fast_calculations
    
    # Use accelerated functions
    result = fast_calculations.matrix_multiply(data)
"""

import logging
import importlib.util
import sys

logger = logging.getLogger(__name__)

# Check if Rust extension is available
try:
    import rust_extensions
    HAS_RUST = True
    logger.info("✅ Rust extensions loaded")
except ImportError:
    HAS_RUST = False
    logger.warning("⚠️ Rust extensions not available (fallback to Python)")

# Check if C++ extension is available
try:
    import cpp_extensions
    HAS_CPP = True
    logger.info("✅ C++ extensions loaded")
except ImportError:
    HAS_CPP = False
    logger.warning("⚠️ C++ extensions not available (fallback to Python)")

# Fallback to pure Python
if not HAS_RUST and not HAS_CPP:
    from . import python_fallback

    def matrix_multiply(data):
        """Fallback to Python implementation"""
        logger.debug("Using Python fallback for matrix_multiply")
        return python_fallback.matrix_multiply(data)

    def detect_smc_patterns(data):
        """Fallback to Python implementation"""
        logger.debug("Using Python fallback for detect_smc_patterns")
        return python_fallback.detect_smc_patterns(data)

    def calculate_volume_profile(data):
        """Fallback to Python implementation"""
        logger.debug("Using Python fallback for calculate_volume_profile")
        return python_fallback.calculate_volume_profile(data)

    def calculate_mcdx(data):
        """Fallback to Python implementation"""
        logger.debug("Using Python fallback for calculate_mcdx")
        return python_fallback.calculate_mcdx(data)

else:
    # Use Rust or C++ extensions
    def matrix_multiply(data):
        if HAS_RUST:
            return rust_extensions.matrix_multiply(data)
        elif HAS_CPP:
            return cpp_extensions.matrix_multiply(data)
        else:
            return python_fallback.matrix_multiply(data)

    def detect_smc_patterns(data):
        if HAS_RUST:
            return rust_extensions.detect_smc_patterns(data)
        elif HAS_CPP:
            return cpp_extensions.detect_smc_patterns(data)
        else:
            return python_fallback.detect_smc_patterns(data)

    def calculate_volume_profile(data):
        if HAS_RUST:
            return rust_extensions.calculate_volume_profile(data)
        elif HAS_CPP:
            return cpp_extensions.calculate_volume_profile(data)
        else:
            return python_fallback.calculate_volume_profile(data)

    def calculate_mcdx(data):
        if HAS_RUST:
            return rust_extensions.calculate_mcdx(data)
        elif HAS_CPP:
            return cpp_extensions.calculate_mcdx(data)
        else:
            return python_fallback.calculate_mcdx(data)

# Expose functions
__all__ = [
    'matrix_multiply',
    'detect_smc_patterns',
    'calculate_volume_profile',
    'calculate_mcdx',
    'HAS_RUST',
    'HAS_CPP'
]
