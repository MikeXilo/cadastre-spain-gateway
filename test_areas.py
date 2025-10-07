#!/usr/bin/env python3
"""
Test different Spanish areas to find ones with cadastral data
"""
import requests
import xml.etree.ElementTree as ET

def test_area(area_name, bbox):
    """Test a specific area for cadastral data"""
    print(f"\n🔍 Testing {area_name}...")
    print(f"BBOX: {bbox}")
    
    params = {
        'service': 'WFS',
        'request': 'GetFeature',
        'version': '2.0.0',
        'typenames': 'cp:CadastralParcel',
        'bbox': f"{bbox},urn:ogc:def:crs:EPSG::4326",
        'outputFormat': 'text/xml; subtype=gml/3.2'
    }
    
    response = requests.get("https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx", 
                          params=params, timeout=30, verify=False)
    
    print(f"Status: {response.status_code}")
    print(f"Response length: {len(response.content)} bytes")
    
    if response.status_code == 200:
        # Check if it's an exception or actual data
        if "ExceptionReport" in response.text:
            try:
                root = ET.fromstring(response.content)
                exception_text = root.find('.//{http://www.opengis.net/ows/1.1}ExceptionText')
                if exception_text is not None:
                    print(f"❌ Exception: {exception_text.text}")
                else:
                    print("❌ Exception (no details)")
            except:
                print("❌ Exception (couldn't parse)")
        else:
            print("✅ Found data!")
            print(f"Response preview: {response.text[:200]}...")
            return True
    else:
        print(f"❌ HTTP Error: {response.status_code}")
    
    return False

def main():
    """Test different Spanish areas"""
    
    # Test areas with different characteristics
    test_areas = [
        ("Madrid Center", "-3.7038,40.4168,-3.7037,40.4169"),  # Very small
        ("Madrid Larger", "-3.8,40.3,-3.6,40.5"),  # Larger Madrid area
        ("Barcelona Center", "2.15,41.38,2.16,41.39"),  # Barcelona center
        ("Barcelona Larger", "2.0,41.3,2.2,41.5"),  # Larger Barcelona area
        ("Seville Center", "-5.99,37.38,-5.98,37.39"),  # Seville center
        ("Seville Larger", "-6.1,37.3,-5.9,37.5"),  # Larger Seville area
        ("Valencia Center", "-0.38,39.47,-0.37,39.48"),  # Valencia center
        ("Valencia Larger", "-0.5,39.4,-0.3,39.6"),  # Larger Valencia area
        ("Bilbao Center", "-2.93,43.26,-2.92,43.27"),  # Bilbao center
        ("Bilbao Larger", "-3.0,43.2,-2.9,43.3"),  # Larger Bilbao area
    ]
    
    print("🇪🇸 Testing Spanish areas for cadastral data...")
    
    successful_areas = []
    
    for area_name, bbox in test_areas:
        if test_area(area_name, bbox):
            successful_areas.append((area_name, bbox))
    
    print(f"\n📊 Results Summary:")
    print(f"Total areas tested: {len(test_areas)}")
    print(f"Areas with data: {len(successful_areas)}")
    
    if successful_areas:
        print("\n✅ Areas with cadastral data:")
        for area_name, bbox in successful_areas:
            print(f"  - {area_name}: {bbox}")
    else:
        print("\n❌ No areas found with cadastral data")
        print("This suggests the WFS service may have limited coverage or different data availability")

if __name__ == "__main__":
    main()
