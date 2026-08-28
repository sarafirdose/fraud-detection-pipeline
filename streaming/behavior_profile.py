"""
Alias export for stream.behavior_profile
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from stream.behavior_profile import AccountProfile, BehavioralProfilerService, behavior_profiler

__all__ = ["AccountProfile", "BehavioralProfilerService", "behavior_profiler"]
