#!/usr/bin/env python3
"""
Check Firecrawl methods and map function capabilities
"""

import os
import sys
sys.path.insert(0, 'src')

from firecrawl import FirecrawlApp

def check_firecrawl_methods():
    """Check what methods are available in FirecrawlApp"""
    
    # Set dummy API key for inspection
    os.environ['FIRECRAWL_API_KEY'] = 'dummy_key_for_inspection'
    
    try:
        firecrawl = FirecrawlApp(api_key='dummy_key_for_inspection')
        
        print("🔍 Available FirecrawlApp methods:")
        print("=" * 50)
        
        methods = [method for method in dir(firecrawl) if not method.startswith('_')]
        for method in methods:
            print(f"  {method}")
        
        # Check if map_url exists and inspect its signature
        if hasattr(firecrawl, 'map_url'):
            print("\n🗺️ Found map_url method!")
            print("=" * 30)
            try:
                help(firecrawl.map_url)
            except Exception as e:
                print(f"Could not get help for map_url: {e}")
        
        # Check if map exists
        if hasattr(firecrawl, 'map'):
            print("\n🗺️ Found map method!")
            print("=" * 30)
            try:
                help(firecrawl.map)
            except Exception as e:
                print(f"Could not get help for map: {e}")
        
        # Check for other mapping-related methods
        mapping_methods = [m for m in methods if 'map' in m.lower()]
        if mapping_methods:
            print(f"\n🗺️ Mapping-related methods: {mapping_methods}")
        
    except Exception as e:
        print(f"Error checking Firecrawl methods: {e}")

if __name__ == "__main__":
    check_firecrawl_methods()