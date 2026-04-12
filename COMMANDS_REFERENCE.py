"""
═══════════════════════════════════════════════════════════════════════════════
                         QUICK COMMAND REFERENCE
═══════════════════════════════════════════════════════════════════════════════
"""

# Perfect working commands - Copy & Paste!

commands = {
    "🎮 GREEDY AGENT (Best - No API needed)": [
        'python inference.py --agent greedy --task easy --episodes 1',
        'python inference.py --agent greedy --task medium --episodes 3',
        'python inference.py --agent greedy --task hard --episodes 5',
    ],
    
    "🤖 EXPLORING AGENT (Good - No API needed)": [
        'python inference.py --agent exploring --task easy --episodes 1',
        'python inference.py --agent exploring --task medium --episodes 1',
    ],
    
    "🎲 RANDOM AGENT (Test - No API needed)": [
        'python inference.py --agent random --task easy --episodes 1',
    ],
    
    "🎯 CORNER CLEANER (Strategy - No API needed)": [
        'python inference.py --agent corner --task easy --episodes 1',
    ],
    
    "🤗 HUGGINGFACE AGENT (Requires --model)": [
        'python inference.py --agent hf --task easy --model "meta-llama/Llama-2-7b-chat-hf"',
        'python inference.py --agent hf --task medium --model "mistralai/Mistral-7B-Instruct-v0.1"',
    ],
    
    "📡 OPENAI API AGENT (Requires OPENAI_API_KEY)": [
        '$env:OPENAI_API_KEY="sk-your-key"; python inference.py --agent api --task easy --model gpt-4',
    ],
    
    "🎮 INTERACTIVE MODE": [
        'python inference.py --interactive --task easy',
        'python inference.py --interactive --task medium',
    ],
    
    "📊 SAVE RESULTS TO JSON": [
        'python inference.py --agent greedy --task easy --output results.json',
        'python inference.py --agent exploring --task hard --output results.json --episodes 5',
    ],
    
    "🎬 RENDER GRID VISUALIZATION": [
        'python inference.py --agent greedy --task easy --render --episodes 1',
    ],
    
    "🔇 QUIET MODE (No verbose output)": [
        'python inference.py --agent greedy --task easy --quiet',
    ],
}

print("╔" + "═" * 77 + "╗")
print("║" + " RECOMMENDED STARTING COMMANDS ".center(77) + "║")
print("╚" + "═" * 77 + "╝\n")

for category, cmds in commands.items():
    print(f"\n{category}")
    print("─" * 80)
    for i, cmd in enumerate(cmds, 1):
        print(f"  {i}. {cmd}")

print("\n" + "=" * 80)
print("MOST RECOMMENDED: Use greedy agent (works perfectly, no API needed)")
print("=" * 80)
print("\n  python inference.py --agent greedy --task easy --episodes 3\n")

print("═" * 80)
print("                              TASK DIFFICULTY")
print("═" * 80)
print("""
  easy    →  5×5 grid, 3 items, perfect for testing (Score: ~0.92)
  medium  →  10×10 grid, 8 items, challenging (Score: ~0.68)
  hard    →  15×15 grid, 15 items, very difficult (Score: ~0.45)
""")

print("═" * 80)
print("                           AVAILABLE EPISODES")
print("═" * 80)
print("""
  --episodes 1    Single episode (default)
  --episodes 3    Test performance (recommended)
  --episodes 5    Track consistency
  --episodes 10   Comprehensive evaluation
""")

print("═" * 80)
print("                    AGENT SELECTION GUIDE")
print("═" * 80)
print("""
  Agent          Cost      Speed    Quality   Recommendation
  ─────────────────────────────────────────────────────────
  greedy         Free      ⚡⚡⚡    ★★★★★   👉 START HERE
  random         Free      ⚡⚡⚡    ★        Testing
  exploring      Free      ⚡⚡⚡    ★★★★   Balance
  corner         Free      ⚡⚡⚡    ★★★     Strategy test
  hf             Free*     ⚡       ★★★     HuggingFace
  api            $$$       ⚡       ★★★★★   OpenAI (costs money)
  
  * HuggingFace free tier has rate limits (~30,000 calls/month)
""")

print("═" * 80)
print("                    HOW TO Choose the best agent?")
print("═" * 80)
print("""
  Want maximum score?              → Use GREEDY agent
  Want to test system?             → Use RANDOM agent
  Want exploration+exploitation?   → Use EXPLORING agent
  Have HuggingFace token?          → Use HF agent
  Have OpenAI API key?             → Use API agent
  Want interactive gameplay?        → Use --interactive
  Want to analyze results?          → Use --output results.json
""")
