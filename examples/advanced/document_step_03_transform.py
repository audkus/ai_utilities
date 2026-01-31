#!/usr/bin/env python3
"""
Document Workflow Step 3: Transform Text

Transform summarized text into different formats using AI Utilities.
"""

from pathlib import Path

from ai_utilities import AiClient, AiSettings
from _common import check_env_vars, get_outputs_dir


def main():
    """Transform text content."""
    print("📄 Document Workflow Step 3: Transform Text")
    print("=" * 50)
    
    # Check for required environment variables
    missing_vars = check_env_vars(['OPENAI_API_KEY'])
    if missing_vars:
        print("❌ Cannot proceed without API key")
        return
    
    # Initialize the AI client
    print("\n🔧 Initializing AI client...")
    try:
        settings = AiSettings()
        client = AiClient(settings)
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # Read summary
    print("\n🎯 Example: Transform Text")
    print("-" * 30)
    
    outputs_dir = get_outputs_dir()
    summary_file = outputs_dir / "text_summary.txt"
    
    if not summary_file.exists():
        print(f"   ❌ Summary file not found: {summary_file}")
        print(f"   💡 Run document_step_02_summarize.py first")
        return
    
    try:
        # Read the summary
        summary = summary_file.read_text(encoding='utf-8')
        print(f"   📖 Read summary from {summary_file}")
        
        # Transform to different formats
        transformations = [
            ("bullet_points", "Convert to bullet points"),
            ("executive_summary", "Create executive summary"),
            ("action_items", "Extract action items")
        ]
        
        for transform_type, description in transformations:
            print(f"\n   🔄 {description}...")
            
            try:
                result = client.transform_text(
                    summary,
                    transformation=transform_type
                )
                
                # Save transformation
                output_file = outputs_dir / f"transformed_{transform_type}.txt"
                output_file.write_text(result, encoding='utf-8')
                print(f"   ✅ Saved to: {output_file}")
                
                # Show preview
                preview = result[:150] + "..." if len(result) > 150 else result
                print(f"   📖 {preview}")
                
            except Exception as e:
                print(f"   ❌ {transform_type} failed: {e}")
        
    except Exception as e:
        print(f"   ❌ Transformation failed: {e}")
    
    print("\n🎉 Step 3 Complete!")
    print("\n💡 Workflow Complete!")
    print("   Check outputs/ directory for all transformed files")


if __name__ == "__main__":
    main()
