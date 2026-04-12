"""Quick test to verify HF_TOKEN configuration."""

import os
import sys

def check_hf_token():
    """Check HF_TOKEN configuration."""
    print("=" * 60)
    print("HF_TOKEN Configuration Check")
    print("=" * 60)
    
    # Check environment variables
    hf_token = os.getenv("HF_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"\n✓ HF_TOKEN found: {bool(hf_token)}")
    if hf_token:
        # Show first 10 and last 4 chars for security
        masked = hf_token[:10] + "..." + hf_token[-4:]
        print(f"  Value: {masked}")
    
    print(f"✓ OPENAI_API_KEY found: {bool(openai_key)}")
    if openai_key:
        masked = openai_key[:10] + "..." + openai_key[-4:]
        print(f"  Value: {masked}")
    
    # Check if OpenAI is installed
    try:
        import openai
        print(f"✓ OpenAI package installed: {openai.__version__}")
    except ImportError:
        print("✗ OpenAI package NOT installed")
        print("  Install: pip install openai")
    
    print("\n" + "=" * 60)
    print("Configuration Summary")
    print("=" * 60)
    
    if hf_token or openai_key:
        print("✅ Ready to use API agent!")
        print("\nRun: python inference.py --agent api --task easy --episodes 1")
    else:
        print("⚠️  No API credentials found")
        print("\nSet HF_TOKEN:")
        print("  PowerShell: $env:HF_TOKEN='your-token'")
        print("  Or: [Environment]::SetEnvironmentVariable('HF_TOKEN', 'your-token', 'User')")
    
    print("=" * 60 + "\n")

if __name__ == "__main__":
    check_hf_token()
