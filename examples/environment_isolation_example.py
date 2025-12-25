"""
Example demonstrating environment variable isolation to prevent contamination.

This example shows how to use the environment utilities to prevent environment
variable contamination between different parts of an application.
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.env_utils import isolated_env_context, cleanup_ai_env_vars
from ai_utilities.client import AiSettings, AiClient
from ai_utilities.config_models import AIConfig


def demonstrate_contamination_problem():
    """Demonstrate the environment variable contamination problem."""
    print("=== Demonstrating Environment Variable Contamination Problem ===")
    
    # Set up initial environment
    os.environ['AI_MODEL'] = 'gpt-4'
    os.environ['AI_TEMPERATURE'] = '0.7'
    
    print(f"Initial environment: AI_MODEL={os.environ['AI_MODEL']}")
    
    # First client uses different settings
    print("\n--- Client 1: High temperature creative writing ---")
    client1_settings = AiSettings()
    print(f"Client 1 model: {client1_settings.model}, temp: {client1_settings.temperature}")
    
    # Simulate environment change for second client
    os.environ['AI_MODEL'] = 'gpt-3.5-turbo'
    os.environ['AI_TEMPERATURE'] = '1.0'
    
    print("\n--- Client 2: Fast responses with gpt-3.5-turbo ---")
    client2_settings = AiSettings()
    print(f"Client 2 model: {client2_settings.model}, temp: {client2_settings.temperature}")
    
    # Problem: Client 1 is now affected by Client 2's environment changes
    print("\n--- Client 1 again (PROBLEM: affected by Client 2) ---")
    client1_settings_again = AiSettings()
    print(f"Client 1 model: {client1_settings_again.model}, temp: {client1_settings_again.temperature}")
    
    print("❌ PROBLEM: Environment variable contamination occurred!")
    
    # Clean up
    cleanup_ai_env_vars()


def demonstrate_isolation_solution():
    """Demonstrate the environment variable isolation solution."""
    print("\n\n=== Demonstrating Environment Variable Isolation Solution ===")
    
    # Set up initial environment
    os.environ['AI_MODEL'] = 'gpt-4'
    os.environ['AI_TEMPERATURE'] = '0.7'
    
    print(f"Initial environment: AI_MODEL={os.environ['AI_MODEL']}")
    
    # First client uses isolated environment
    print("\n--- Client 1: High temperature creative writing (Isolated) ---")
    with isolated_env_context({
        'AI_MODEL': 'gpt-4',
        'AI_TEMPERATURE': '0.9',
        'AI_MAX_TOKENS': '2000'
    }):
        client1_settings = AiSettings()
        print(f"Client 1 model: {client1_settings.model}, temp: {client1_settings.temperature}")
        print(f"Client 1 max tokens: {client1_settings.max_tokens}")
    
    # Second client uses different isolated environment
    print("\n--- Client 2: Fast responses with gpt-3.5-turbo (Isolated) ---")
    with isolated_env_context({
        'AI_MODEL': 'gpt-3.5-turbo',
        'AI_TEMPERATURE': '0.1',
        'AI_TIMEOUT': '10'
    }):
        client2_settings = AiSettings()
        print(f"Client 2 model: {client2_settings.model}, temp: {client2_settings.temperature}")
        print(f"Client 2 timeout: {client2_settings.timeout}")
    
    # Original environment is preserved
    print("\n--- Original environment preserved ---")
    print(f"Original AI_MODEL: {os.environ['AI_MODEL']}")
    print(f"Original AI_TEMPERATURE: {os.environ['AI_TEMPERATURE']}")
    
    print("✅ SUCCESS: No environment variable contamination!")
    
    # Clean up
    cleanup_ai_env_vars()


def demonstrate_multi_tenant_application():
    """Demonstrate environment isolation in a multi-tenant application."""
    print("\n\n=== Multi-Tenant Application Example ===")
    
    def process_tenant_request(tenant_id: str, model: str, temperature: float):
        """Process request for a specific tenant with isolated environment."""
        print(f"\n--- Processing request for {tenant_id} ---")
        
        # Each tenant gets isolated environment
        with isolated_env_context({
            'AI_MODEL': model,
            'AI_TEMPERATURE': str(temperature),
            'AI_API_KEY': f'api_key_{tenant_id}'  # Tenant-specific API key
        }):
            settings = AiSettings()
            client = AiClient(settings)
            
            print(f"Tenant: {tenant_id}")
            print(f"Model: {settings.model}")
            print(f"Temperature: {settings.temperature}")
            print(f"API Key: {settings.api_key[:10]}...")  # Show partial key
            
            # Simulate processing
            return f"Response for {tenant_id} using {settings.model}"
    
    # Process requests for different tenants
    tenants = [
        ('tenant_a', 'gpt-4', 0.7),
        ('tenant_b', 'gpt-3.5-turbo', 0.3),
        ('tenant_c', 'gpt-4', 0.9)
    ]
    
    for tenant_id, model, temp in tenants:
        result = process_tenant_request(tenant_id, model, temp)
        print(f"Result: {result}")
    
    print("\n✅ All tenant requests processed with complete environment isolation!")


def demonstrate_config_isolation():
    """Demonstrate AIConfig isolation for different deployment scenarios."""
    print("\n\n=== AIConfig Isolation Example ===")
    
    scenarios = [
        ('Development', {
            'AI_MODEL_RPM': '100',
            'AI_MODEL_TPM': '10000',
            'AI_MODEL_TPD': '1000000',
            'AI_GPT_4_RPM': '50'
        }),
        ('Staging', {
            'AI_MODEL_RPM': '500',
            'AI_MODEL_TPM': '50000',
            'AI_MODEL_TPD': '5000000',
            'AI_GPT_4_RPM': '200'
        }),
        ('Production', {
            'AI_MODEL_RPM': '1000',
            'AI_MODEL_TPM': '100000',
            'AI_MODEL_TPD': '10000000',
            'AI_GPT_4_RPM': '500'
        })
    ]
    
    for env_name, env_vars in scenarios:
        print(f"\n--- {env_name} Environment ---")
        
        with isolated_env_context(env_vars):
            config = AIConfig()
            
            print(f"gpt-3.5-turbo RPM: {config.models['gpt-3.5-turbo'].requests_per_minute}")
            print(f"gpt-4 RPM: {config.models['gpt-4'].requests_per_minute}")
            print(f"gpt-4-turbo RPM: {config.models['gpt-4-turbo'].requests_per_minute}")
    
    print("\n✅ All environments configured with complete isolation!")


def demonstrate_error_handling():
    """Demonstrate proper error handling with environment isolation."""
    print("\n\n=== Error Handling with Environment Isolation ===")
    
    # Set up initial environment
    os.environ['AI_MODEL'] = 'gpt-4'
    os.environ['AI_TEMPERATURE'] = '0.7'
    
    try:
        print("Attempting operation with isolated environment...")
        
        with isolated_env_context({
            'AI_MODEL': 'gpt-3.5-turbo',
            'AI_TEMPERATURE': '1.5'  # This might cause issues
        }):
            settings = AiSettings()
            print(f"Settings created: model={settings.model}, temp={settings.temperature}")
            
            # Simulate an error
            raise ValueError("Simulated application error")
            
    except ValueError as e:
        print(f"Caught error: {e}")
    
    # Verify original environment is restored even after error
    print(f"Environment restored: AI_MODEL={os.environ['AI_MODEL']}")
    print(f"Environment restored: AI_TEMPERATURE={os.environ['AI_TEMPERATURE']}")
    
    print("✅ Environment properly restored after error!")
    
    # Clean up
    cleanup_ai_env_vars()


def main():
    """Run all examples."""
    print("Environment Variable Isolation Examples")
    print("=" * 50)
    
    # Demonstrate the problem
    demonstrate_contamination_problem()
    
    # Demonstrate the solution
    demonstrate_isolation_solution()
    
    # Multi-tenant application example
    demonstrate_multi_tenant_application()
    
    # Configuration isolation example
    demonstrate_config_isolation()
    
    # Error handling example
    demonstrate_error_handling()
    
    print("\n" + "=" * 50)
    print("All examples completed successfully!")
    print("\nKey Benefits:")
    print("✅ Prevents environment variable contamination")
    print("✅ Enables safe multi-tenant applications")
    print("✅ Supports different deployment scenarios")
    print("✅ Provides proper error handling and cleanup")
    print("✅ Maintains application reliability and consistency")


if __name__ == '__main__':
    main()
