#!/usr/bin/env python3
"""
Test MCP integration with the agent
Verifies all MCP tools are working correctly
"""

from agent_langgraph import ask_langgraph_agent
import json

def test_fda_drug_info():
    """Test FDA drug information retrieval"""
    print("=" * 60)
    print("TEST 1: FDA Drug Information (Morphine)")
    print("=" * 60)
    
    result = ask_langgraph_agent("What are the warnings for morphine?")
    
    print(f"✓ Success: {result.get('success')}")
    print(f"✓ Tool calls: {[tc['tool'] for tc in result.get('tool_calls', [])]}")
    print(f"✓ Answer length: {len(result['answer'])} chars")
    print(f"✓ Answer preview: {result['answer'][:300]}...")
    print()
    
    # Check if FDA tool was called
    fda_called = any('fda' in tc['tool'].lower() for tc in result.get('tool_calls', []))
    print(f"{'✅' if fda_called else '❌'} FDA tool was called: {fda_called}")
    print()

def test_medical_literature():
    """Test PubMed literature search"""
    print("=" * 60)
    print("TEST 2: Medical Literature Search (Paracetamol pregnancy)")
    print("=" * 60)
    
    result = ask_langgraph_agent("Find recent studies about paracetamol safety during pregnancy")
    
    print(f"✓ Success: {result.get('success')}")
    print(f"✓ Tool calls: {[tc['tool'] for tc in result.get('tool_calls', [])]}")
    print(f"✓ Answer length: {len(result['answer'])} chars")
    print(f"✓ Answer preview: {result['answer'][:300]}...")
    print()
    
    # Check if literature search was called
    lit_called = any('literature' in tc['tool'].lower() or 'pubmed' in tc['tool'].lower() 
                     for tc in result.get('tool_calls', []))
    print(f"{'✅' if lit_called else '❌'} Literature search was called: {lit_called}")
    print()

def test_drug_recalls():
    """Test FDA drug recalls check"""
    print("=" * 60)
    print("TEST 3: Drug Recalls Check (Aspirin)")
    print("=" * 60)
    
    result = ask_langgraph_agent("Are there any recalls for aspirin?")
    
    print(f"✓ Success: {result.get('success')}")
    print(f"✓ Tool calls: {[tc['tool'] for tc in result.get('tool_calls', [])]}")
    print(f"✓ Answer length: {len(result['answer'])} chars")
    p