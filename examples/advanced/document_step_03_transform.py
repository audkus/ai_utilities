#!/usr/bin/env python3
"""
Document Workflow Step 3: Transform Text

Transform summarized text into different formats using AI Utilities.
"""

from pathlib import Path
import sys

# === BOOTSTRAP: Ensure ai_utilities is importable from any location ===
script_path = Path(__file__).resolve()
repo_root = script_path.parent.parent.parent

# Add src directory to sys.path if not already there
src_dir = repo_root / "src"
src_dir_str = str(src_dir)
if src_dir_str not in sys.path:
    sys.path.insert(0, src_dir_str)

# Add repo root to sys.path for examples import
repo_root_str = str(repo_root)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

from examples._common import print_header, output_dir, require_env, assets_dir
# === END BOOTSTRAP ===

from ai_utilities import AiClient, AiSettings


def main():
    """Transform text content."""
    
    print_header("📄 Document Workflow Step 3: Transform Text")
    
    # Check for required environment variables
    if not require_env(['OPENAI_API_KEY']):
        print("❌ CONFIGURATION REQUIRED - Cannot proceed without API key")
        return 1
    
    # Initialize AI client
    print("\n🔧 Initializing AI client...")
    try:
        client = AiClient()
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return 1
    
    # Use asset from examples/assets directory
    document_file = assets_dir() / "sample_document.pdf"
    print(f"\n📄 Processing document: {document_file}")
    
    # Check if document file exists
    if not document_file.exists():
        print(f"❌ Document file not found: {document_file}")
        print("💡 Make sure sample_document.pdf exists in examples/assets/")
        return 1
    
    try:
        # Upload the document
        print("   Uploading document...")
        uploaded_file = client.upload_file(str(document_file), purpose="assistants")
        print(f"✅ Document uploaded: {uploaded_file.file_id}")
        
        # Transform to different formats
        script_output_dir = output_dir(Path(__file__))
        
        # 1. Executive Summary
        print("   Generating executive summary...")
        exec_summary_prompt = f"""
        Transform document {uploaded_file.file_id} into a concise executive summary.
        Include:
        - Key findings (3-5 bullet points)
        - Main recommendations (2-3 bullet points)
        - Overall conclusion (1-2 sentences)
        
        Format as a professional executive summary for busy executives.
        Keep it under 200 words.
        """
        
        exec_summary = client.ask(exec_summary_prompt)
        exec_summary_file = script_output_dir / "executive_summary.txt"
        exec_summary_file.write_text(exec_summary, encoding='utf-8')
        print(f"✅ Executive summary saved to: {exec_summary_file}")
        
        # 2. Blog Post
        print("   Generating blog post...")
        blog_prompt = f"""
        Transform document {uploaded_file.file_id} into an engaging blog post.
        Include:
        - Catchy title
        - Brief introduction
        - 3-4 main sections with headings
        - Conclusion with call to action
        
        Write in a conversational, engaging tone suitable for a general audience.
        Aim for 500-800 words.
        """
        
        blog_post = client.ask(blog_prompt)
        blog_file = script_output_dir / "blog_post.txt"
        blog_file.write_text(blog_post, encoding='utf-8')
        print(f"✅ Blog post saved to: {blog_file}")
        
        # 3. Technical Report
        print("   Generating technical report...")
        tech_prompt = f"""
        Transform document {uploaded_file.file_id} into a technical report.
        Include:
        - Abstract
        - Methodology
        - Results with data points
        - Technical analysis
        - Recommendations
        
        Use formal, technical language suitable for engineers and researchers.
        Include specific details and measurements where possible.
        """
        
        tech_report = client.ask(tech_prompt)
        tech_file = script_output_dir / "technical_report.txt"
        tech_file.write_text(tech_report, encoding='utf-8')
        print(f"✅ Technical report saved to: {tech_file}")
        
        # 4. Presentation Outline
        print("   Generating presentation outline...")
        pres_prompt = f"""
        Transform document {uploaded_file.file_id} into a presentation outline.
        Include:
        - Slide 1: Title and subtitle
        - Slide 2: Agenda/Overview
        - 5-7 content slides with bullet points
        - Final slide: Conclusion and next steps
        
        Format each slide clearly with "Slide X:" heading.
        Keep content concise and suitable for presentation format.
        """
        
        presentation = client.ask(pres_prompt)
        pres_file = script_output_dir / "presentation_outline.txt"
        pres_file.write_text(presentation, encoding='utf-8')
        print(f"✅ Presentation outline saved to: {pres_file}")
        
        # Show transformation summary
        print(f"\n📊 Transformation Summary:")
        print(f"   Document: {document_file.name}")
        print(f"   File ID: {uploaded_file.file_id}")
        print(f"   Formats generated: 4")
        print(f"   Output directory: {script_output_dir}")
        
        generated_files = [
            ("Executive Summary", exec_summary_file, len(exec_summary)),
            ("Blog Post", blog_file, len(blog_post)),
            ("Technical Report", tech_file, len(tech_report)),
            ("Presentation", pres_file, len(presentation))
        ]
        
        print(f"\n📝 Generated Files:")
        for name, file_path, length in generated_files:
            print(f"   - {name}: {length} characters")
        
        # Show preview of executive summary
        preview_lines = exec_summary.splitlines()[:5]
        print(f"\n📝 Executive Summary Preview:")
        for i, line in enumerate(preview_lines, 1):
            print(f"   {i}: {line[:80]}{'...' if len(line) > 80 else ''}")
        
    except Exception as e:
        print(f"❌ Text transformation failed: {e}")
        return 1
    
    print(f"\n🎉 Document transformation complete!")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
