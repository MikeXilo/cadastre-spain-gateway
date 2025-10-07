#!/usr/bin/env python3
"""
Test script to investigate Spanish Cadastre WFS capabilities
"""
import requests
from owslib.wfs import WebFeatureService
import xml.etree.ElementTree as ET

def test_wfs_capabilities():
    """Test the WFS GetCapabilities request"""
    wfs_url = "https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx"
    
    print("🔍 Testing Spanish Cadastre WFS...")
    print(f"URL: {wfs_url}")
    
    try:
        # Test GetCapabilities
        print("\n1. Testing GetCapabilities...")
        caps_url = f"{wfs_url}?service=WFS&request=GetCapabilities&VERSION=2.0.0"
        print(f"Requesting: {caps_url}")
        
        response = requests.get(caps_url, timeout=30, verify=False)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ GetCapabilities successful!")
            
            # Parse the capabilities
            root = ET.fromstring(response.content)
            
            # Find available feature types
            feature_types = root.findall('.//{http://www.opengis.net/wfs/2.0}FeatureType')
            print(f"\n📋 Available Feature Types ({len(feature_types)}):")
            for ft in feature_types:
                name = ft.find('.//{http://www.opengis.net/wfs/2.0}Name')
                title = ft.find('.//{http://www.opengis.net/wfs/2.0}Title')
                if name is not None:
                    print(f"  - {name.text}")
                    if title is not None:
                        print(f"    Title: {title.text}")
        else:
            print(f"❌ GetCapabilities failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_wfs_client():
    """Test using OWSLib WFS client"""
    print("\n2. Testing with OWSLib client...")
    
    try:
        wfs = WebFeatureService(url="https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx", version='2.0.0')
        print("✅ WFS client initialized")
        
        # List available feature types
        print(f"Available feature types: {list(wfs.contents.keys())}")
        
        # Get feature type details
        for feature_type in wfs.contents:
            print(f"\nFeature Type: {feature_type}")
            ft = wfs.contents[feature_type]
            print(f"  Title: {ft.title}")
            print(f"  Abstract: {ft.abstract}")
            
    except Exception as e:
        print(f"❌ OWSLib error: {e}")

def test_simple_getfeature():
    """Test a simple GetFeature request"""
    print("\n3. Testing simple GetFeature request...")
    
    try:
        # Try a very small bounding box in Madrid
        bbox = "-3.7038,40.4168,-3.7037,40.4169"  # Very small area in Madrid center
        
        params = {
            'service': 'WFS',
            'request': 'GetFeature',
            'version': '2.0.0',
            'typenames': 'CP.CadastralParcel',
            'bbox': f"{bbox},urn:ogc:def:crs:EPSG::4326",
            'outputFormat': 'application/json'  # Try JSON instead of GML
        }
        
        response = requests.get("https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx", 
                              params=params, timeout=30, verify=False)
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"Response length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("✅ GetFeature request successful!")
            print(f"Response preview: {response.text[:200]}...")
        else:
            print(f"❌ GetFeature failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ GetFeature error: {e}")

if __name__ == "__main__":
    test_wfs_capabilities()
    test_wfs_client()
    test_simple_getfeature()
