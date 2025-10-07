#!/usr/bin/env python3
"""
Debug the WFS exception to understand what's wrong
"""
import requests
import xml.etree.ElementTree as ET

def debug_wfs_exception():
    """Debug the WFS exception response"""
    
    # Try the same request that failed
    bbox = "-3.7038,40.4168,-3.7037,40.4169"
    
    params = {
        'service': 'WFS',
        'request': 'GetFeature',
        'version': '2.0.0',
        'typenames': 'CP.CadastralParcel',  # Try with CP: prefix
        'bbox': f"{bbox},urn:ogc:def:crs:EPSG::4326",
        'outputFormat': 'application/json'
    }
    
    response = requests.get("https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx", 
                          params=params, timeout=30, verify=False)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Parse the exception
    try:
        root = ET.fromstring(response.content)
        exception_text = root.find('.//{http://www.opengis.net/ows/1.1}ExceptionText')
        if exception_text is not None:
            print(f"\nException details: {exception_text.text}")
    except:
        pass

def test_different_parameters():
    """Test with different parameter combinations"""
    
    print("\n🔍 Testing different parameter combinations...")
    
    # Test 1: Use cp: prefix
    print("\n1. Testing with cp: prefix...")
    params1 = {
        'service': 'WFS',
        'request': 'GetFeature',
        'version': '2.0.0',
        'typenames': 'cp:CadastralParcel',
        'bbox': "-3.7038,40.4168,-3.7037,40.4169,urn:ogc:def:crs:EPSG::4326",
        'outputFormat': 'application/json'
    }
    
    response1 = requests.get("https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx", 
                           params=params1, timeout=30, verify=False)
    print(f"Status: {response1.status_code}")
    print(f"Response length: {len(response1.content)}")
    if response1.status_code != 200:
        print(f"Error: {response1.text[:200]}...")
    
    # Test 2: Try GML output
    print("\n2. Testing with GML output...")
    params2 = {
        'service': 'WFS',
        'request': 'GetFeature',
        'version': '2.0.0',
        'typenames': 'cp:CadastralParcel',
        'bbox': "-3.7038,40.4168,-3.7037,40.4169,urn:ogc:def:crs:EPSG::4326",
        'outputFormat': 'text/xml; subtype=gml/3.2'
    }
    
    response2 = requests.get("https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx", 
                           params=params2, timeout=30, verify=False)
    print(f"Status: {response2.status_code}")
    print(f"Response length: {len(response2.content)}")
    if response2.status_code != 200:
        print(f"Error: {response2.text[:200]}...")
    else:
        print("✅ GML request successful!")
        print(f"Response preview: {response2.text[:300]}...")
    
    # Test 3: Try different bounding box format
    print("\n3. Testing different bbox format...")
    params3 = {
        'service': 'WFS',
        'request': 'GetFeature',
        'version': '2.0.0',
        'typenames': 'cp:CadastralParcel',
        'bbox': "-3.7038,40.4168,-3.7037,40.4169",  # No CRS in bbox
        'outputFormat': 'text/xml; subtype=gml/3.2'
    }
    
    response3 = requests.get("https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx", 
                           params=params3, timeout=30, verify=False)
    print(f"Status: {response3.status_code}")
    print(f"Response length: {len(response3.content)}")
    if response3.status_code != 200:
        print(f"Error: {response3.text[:200]}...")
    else:
        print("✅ Different bbox format successful!")
        print(f"Response preview: {response3.text[:300]}...")

if __name__ == "__main__":
    debug_wfs_exception()
    test_different_parameters()
