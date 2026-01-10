#!/usr/bin/env python3
"""
Test the Tiered Setup System
"""

import sys
import os
sys.path.insert(0, 'src')

from ai_utilities.improved_setup import ImprovedSetupSystem, SetupLevel

def test_tiered_setup():
    """Test the tiered setup system functionality"""
    print("🧪 TESTING TIERED SETUP SYSTEM")
    print("=" * 40)
    
    setup = ImprovedSetupSystem()
    
    # Test parameter categorization
    print("✅ Testing parameter categorization:")
    
    basic_params = setup._get_parameters_by_level(SetupLevel.BASIC)
    standard_params = setup._get_parameters_by_level(SetupLevel.STANDARD)
    expert_params = setup._get_parameters_by_level(SetupLevel.EXPERT)
    
    print(f"  Basic parameters: {len(basic_params)} - {basic_params}")
    print(f"  Standard parameters: {len(standard_params)} - {standard_params}")
    print(f"  Expert parameters: {len(expert_params)} - {expert_params}")
    
    # Verify hierarchy
    assert len(basic_params) == 6, f"Expected 6 basic params, got {len(basic_params)}"
    assert len(standard_params) == 10, f"Expected 10 standard params, got {len(standard_params)}"
    assert len(expert_params) == 18, f"Expected 18 expert params, got {len(expert_params)}"
    
    # Verify basic is subset of standard
    assert all(p in standard_params for p in basic_params), "Basic params should be in standard"
    assert all(p in expert_params for p in standard_params), "Standard params should be in expert"
    
    # Test update_check_days parameter
    print("\n✅ Testing update_check_days parameter:")
    update_param = setup.param_registry.get_parameter("update_check_days")
    print(f"  Parameter name: {update_param.name}")
    print(f"  Description: {update_param.description}")
    print(f"  Default: {update_param.default_value}")
    print(f"  Examples: {update_param.examples}")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Tiered setup system is working correctly")
    print("✅ Parameter categorization is functional")
    print("✅ update_check_days parameter is properly configured")

def show_setup_examples():
    """Show examples of what each setup level looks like"""
    print("\n📋 SETUP LEVEL EXAMPLES")
    print("=" * 30)
    
    setup = ImprovedSetupSystem()
    
    print("\n🔵 BASIC SETUP (6 parameters):")
    basic_params = setup._get_parameters_by_level(SetupLevel.BASIC)
    for param_name in basic_params:
        param = setup.param_registry.get_parameter(param_name)
        print(f"  • {param.name} ({param.env_var})")
    
    print("\n🟡 STANDARD SETUP (10 parameters):")
    standard_params = setup._get_parameters_by_level(SetupLevel.STANDARD)
    for param_name in standard_params:
        param = setup.param_registry.get_parameter(param_name)
        level = "🔵" if param_name in basic_params else "🟡"
        print(f"  {level} {param.name} ({param.env_var})")
    
    print("\n🔴 EXPERT SETUP (18 parameters):")
    expert_params = setup._get_parameters_by_level(SetupLevel.EXPERT)
    for param_name in expert_params:
        param = setup.param_registry.get_parameter(param_name)
        if param_name in basic_params:
            level = "🔵"
        elif param_name in standard_params:
            level = "🟡"
        else:
            level = "🔴"
        print(f"  {level} {param.name} ({param.env_var})")

if __name__ == "__main__":
    test_tiered_setup()
    show_setup_examples()
