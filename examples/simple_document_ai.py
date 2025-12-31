#!/usr/bin/env python3
"""
Simple Document AI Example

Shows the basic workflow: Upload document → Ask AI questions about it
"""

from ai_utilities import AiClient


def analyze_document():
    """Simple document analysis workflow."""
    
    # 1. Initialize AI client
    client = AiClient()
    
    # 2. Upload your document
    print("Uploading document...")
    uploaded_file = client.upload_file(
        "my_document.pdf",  # Path to your document
        purpose="assistants"
    )
    print(f"✅ Document uploaded: {uploaded_file.file_id}")
    
    # 3. Ask AI to analyze the document
    print("Analyzing document...")
    summary = client.ask(
        f"Please summarize the document {uploaded_file.file_id} "
        "and extract the key points."
    )
    print("Summary:")
    print(summary)
    
    # 4. Ask follow-up questions
    print("\nAsking follow-up questions...")
    insights = client.ask(
        f"Based on document {uploaded_file.file_id}, "
        "what are the main insights or recommendations?"
    )
    print("Insights:")
    print(insights)


if __name__ == "__main__":
    analyze_document()
