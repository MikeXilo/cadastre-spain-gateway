import os
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from owslib.wfs import WebFeatureService
from io import BytesIO
from lxml import etree
import json
from geojson import FeatureCollection, Feature, Polygon
from pyproj import CRS, Transformer
import math

app = FastAPI()

# --- Configuration ---
# Spanish Cadastre WFS URL for Cadastral Parcels (CP)
CATASTRO_WFS_URL = "https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx"

# Define CRS for transformations
# WGS84 (latitude, longitude) - commonly used for input
CRS_WGS84 = CRS("EPSG:4326")
# ETRS89 UTM Zone 30 - used by Spanish Cadastre WFS
CRS_ETRS89_UTM30 = CRS("EPSG:25830")

# Create transformers for coordinate conversion
transformer_wgs84_to_utm30 = Transformer.from_crs(CRS_WGS84, CRS_ETRS89_UTM30, always_xy=True)
transformer_utm30_to_wgs84 = Transformer.from_crs(CRS_ETRS89_UTM30, CRS_WGS84, always_xy=True)

# Allow CORS for development/production
# You should lock this down to your frontend's domain in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def gml_to_geojson_lite(gml_bytes):
    """
    Parses Catastro's GML response and extracts coordinates into GeoJSON format.
    Handles coordinate transformation from ETRS89 UTM Zone 30 to WGS84.
    """
    try:
        # 1. Parse GML
        root = etree.fromstring(gml_bytes)
        
        # 2. Define namespaces used by Catastro (updated based on actual response)
        CP_NAMESPACE = 'http://inspire.ec.europa.eu/schemas/cp/4.0'
        GML_NAMESPACE = 'http://www.opengis.net/gml/3.2'
        
        ns = {
            'wfs': 'http://www.opengis.net/wfs/2.0',
            'gml': GML_NAMESPACE,
            'cp': CP_NAMESPACE,
            'sgo': 'http://www.opengis.net/sgo', # Sometimes used for geometry
            'CP': CP_NAMESPACE
        }
        
        features = []
        
        # Check for WFS exception report first
        exception_report = root.find('.//wfs:ExceptionReport', ns)
        if exception_report is not None:
            exception_text = exception_report.find('.//wfs:ExceptionText', ns)
            if exception_text is not None:
                print(f"WFS Exception: {exception_text.text}")
                return FeatureCollection([]) # Return empty if WFS reports an exception
        
        # DEBUG: Let's see what's actually in the XML
        print("DEBUG: Looking for features...")
        all_elements = root.findall('.//*')
        print(f"Total elements in XML: {len(all_elements)}")
        
        # Look for any elements with 'parcel' in the name
        parcel_elements = [elem for elem in all_elements if 'parcel' in elem.tag.lower()]
        print(f"Elements with 'parcel' in name: {len(parcel_elements)}")
        if parcel_elements:
            print(f"First parcel element: {parcel_elements[0].tag}")
        
        # 3. Find all Cadastral Parcel features (try both namespace variations)
        cp_features1 = root.findall('.//cp:CadastralParcel', ns)
        cp_features2 = root.findall('.//CP:CadastralParcel', ns)
        print(f"Found cp:CadastralParcel: {len(cp_features1)}")
        print(f"Found CP:CadastralParcel: {len(cp_features2)}")
        
        for i, cp_feature in enumerate(cp_features1 or cp_features2):
            print(f"Processing feature {i+1}...")
            
            # Find the geometry container (cp:geometry)
            geometry_container = cp_feature.find(f'{{{CP_NAMESPACE}}}geometry')
            print(f"  Geometry container found: {geometry_container is not None}")
            
            if geometry_container is not None:
                # Find the GML surface (try MultiSurface first, then Surface, then Polygon)
                gml_surface = (geometry_container.find(f'{{{GML_NAMESPACE}}}MultiSurface') or
                              geometry_container.find(f'{{{GML_NAMESPACE}}}Surface') or
                              geometry_container.find(f'{{{GML_NAMESPACE}}}Polygon'))
                
                print(f"  GML surface found: {gml_surface is not None}")
                
                if gml_surface is not None:
                    # Find the posList node
                    pos_list = gml_surface.find(f'.//{{{GML_NAMESPACE}}}posList')
                    print(f"  posList found: {pos_list is not None}")
                    
                    if pos_list is not None and pos_list.text:
                        coordinates_str = pos_list.text.strip()
                        print(f"  Coordinates length: {len(coordinates_str)}")
                    
                    # Split and convert to floats
                    coords = [float(c) for c in coordinates_str.split()]
                    
                    # Coordinates from UTM are typically x y x y ... (Easting Northing)
                    # We need to convert them to (longitude, latitude) for GeoJSON
                    utm_coords = []
                    for i in range(0, len(coords), 2):
                        if i + 1 < len(coords):
                            easting = coords[i]
                            northing = coords[i + 1]
                            utm_coords.append((easting, northing))
                    
                    if utm_coords:
                        # Transform UTM coordinates to WGS84 (lon, lat)
                        wgs84_coords = [transformer_utm30_to_wgs84.transform(x, y) for x, y in utm_coords]
                        
                        # Create GeoJSON polygon
                        geojson_polygon = Polygon([wgs84_coords])
                        
                        # Extract properties
                        cadastral_id = cp_feature.get('{http://www.opengis.net/gml/3.2}id', 'unknown')
                        
                        # Try to extract cadastral reference and area from the feature
                        cadastral_reference = 'unknown'
                        area_value = 0.0
                        
                        # Look for cadastral reference in various possible locations
                        ref_elements = [
                            cp_feature.find(f'{{{CP_NAMESPACE}}}nationalCadastralReference'),
                            cp_feature.find(f'{{{CP_NAMESPACE}}}localId'),
                            cp_feature.find(f'{{{CP_NAMESPACE}}}inspireId')
                        ]
                        
                        for ref_elem in ref_elements:
                            if ref_elem is not None and ref_elem.text:
                                cadastral_reference = ref_elem.text.strip()
                                break
                        
                        # Look for area value
                        area_elem = cp_feature.find(f'{{{CP_NAMESPACE}}}areaValue')
                        if area_elem is not None and area_elem.text:
                            try:
                                area_value = float(area_elem.text.strip())
                            except ValueError:
                                area_value = 0.0
                        
                        # Calculate area in square meters and hectares
                        area_sqm = area_value if area_value > 0 else 0
                        area_hectares = area_sqm / 10000 if area_sqm > 0 else 0
                        
                        feature = Feature(geometry=geojson_polygon, properties={
                            "cadastral_id": cadastral_id,
                            "cadastral_reference": cadastral_reference,
                            "area_sqm": area_sqm,
                            "area_hectares": area_hectares,
                            "country": "spain"
                        })
                        features.append(feature)

        return FeatureCollection(features)
    
    except Exception as e:
        print(f"Error during GML parsing: {e}")
        print(f"GML content preview: {gml_bytes[:500]}...")
        # Return an empty GeoJSON feature collection on error
        return FeatureCollection([])

@app.get("/api/catastro-plots")
async def get_catastro_plots(
    # Expects a comma-separated string: minX, minY, maxX, maxY (WGS84/EPSG:4326)
    bbox: str = Query(..., description="Bounding box in WGS84: minLon,minLat,maxLon,maxLat")
):
    """
    Queries the Spanish Cadastre WFS for cadastral plots within a given BBOX.
    Converts WGS84 coordinates to ETRS89 UTM Zone 30 for the WFS query.
    Converts the GML response to GeoJSON before returning to the client.
    """
    try:
        # Parse the WGS84 bounding box
        min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(','))
        
        # Transform WGS84 coordinates to ETRS89 UTM Zone 30
        min_easting, min_northing = transformer_wgs84_to_utm30.transform(min_lon, min_lat)
        max_easting, max_northing = transformer_wgs84_to_utm30.transform(max_lon, max_lat)
        
        # Construct the bbox string for the WFS request in ETRS89 UTM Zone 30
        # WFS BBOX format is typically minx,miny,maxx,maxy,CRS
        # For UTM, x is Easting, y is Northing
        utm_bbox_str = f"{min_easting},{min_northing},{max_easting},{max_northing},urn:ogc:def:crs:EPSG::25830"
        
        print(f"Original WGS84 bbox: {bbox}")
        print(f"Transformed UTM bbox: {utm_bbox_str}")
        
        # 1. Initialize WFS Client (This is mainly to ensure connection/discovery)
        wfs = WebFeatureService(url=CATASTRO_WFS_URL, version='2.0.0')
        
        # 2. Construct the GetFeature request with UTM coordinates
        # CRITICAL FIX: Use the exact format from official documentation
        WFS_TYPENAME = 'cp.cadastralparcel'  # <-- Official format: lowercase with dots
        
        # Use the exact BBOX format from documentation (no CRS in bbox, separate SRSname)
        utm_bbox_str = f"{min_easting},{min_northing},{max_easting},{max_northing}"
        
        response = requests.get(
            CATASTRO_WFS_URL,
            params={
                'service': 'wfs',  # lowercase as in documentation
                'request': 'getfeature',  # lowercase as in documentation
                'version': '2.0.0',
                'Typenames': WFS_TYPENAME,  # Exact case from documentation
                'SRSname': 'EPSG::25830',  # Add SRSname parameter as required
                'bbox': utm_bbox_str,  # BBOX without CRS (SRSname handles it)
                'outputFormat': 'text/xml; subtype=gml/3.2' # Specify GML output
            },
            # Catastro has SSL issues sometimes, verify=False helps in case of cert errors (use with caution)
            verify=False 
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Catastro WFS request failed: {response.status_code}")
            
        # DEBUG: Check what we're actually getting
        print("=" * 50)
        print("DEBUG: WFS Response Analysis")
        print("=" * 50)
        print(f"Response status: {response.status_code}")
        print(f"Response length: {len(response.content)} bytes")
        print(f"Response content type: {response.headers.get('content-type', 'unknown')}")
        print("Response preview:")
        print(response.text[:500])
        print("=" * 50)
            
        # 3. Process GML into GeoJSON
        geojson_data = gml_to_geojson_lite(response.content)
        
        print(f"Parsed features count: {len(geojson_data.get('features', []))}")
        print("=" * 50)

        return geojson_data

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid BBOX format. Must be minLon,minLat,maxLon,maxLat.")
    except Exception as e:
        # Log the full exception for debugging
        print(f"Server error during cadastral query: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred processing the Catastro data: {e}")

@app.get("/api/catastro-parcel")
async def get_catastro_parcel(
    refcat: str = Query(..., description="14-digit cadastral reference (e.g., 3662001TF3136S)")
):
    """
    Get a specific cadastral parcel by its reference using GetParcel stored query.
    """
    try:
        # Use the GetParcel stored query
        response = requests.get(
            CATASTRO_WFS_URL,
            params={
                'service': 'wfs',
                'version': '2',
                'request': 'getfeature',
                'STOREDQUERIE_ID': 'GetParcel',
                'refcat': refcat,
                'srsname': 'EPSG::25830'
            },
            verify=False
        )

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Catastro WFS request failed: {response.status_code}")

        # Process GML into GeoJSON
        geojson_data = gml_to_geojson_lite(response.content)
        return geojson_data

    except Exception as e:
        print(f"Server error during parcel query: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying parcel: {e}")


@app.get("/api/catastro-zone")
async def get_catastro_zone(
    cod_zona: str = Query(..., description="Zone code (12 digits urban, 9 digits rural)")
):
    """
    Get cadastral zoning information using GetZoning stored query.
    """
    try:
        # Use the GetZoning stored query
        response = requests.get(
            CATASTRO_WFS_URL,
            params={
                'service': 'wfs',
                'version': '2',
                'request': 'getfeature',
                'STOREDQUERIE_ID': 'GetZoning',
                'cod_zona': cod_zona,
                'srsname': 'EPSG::25830'
            },
            verify=False
        )

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Catastro WFS request failed: {response.status_code}")

        # Process GML into GeoJSON
        geojson_data = gml_to_geojson_lite(response.content)
        return geojson_data

    except Exception as e:
        print(f"Server error during zone query: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying zone: {e}")


@app.get("/api/catastro-parcels-by-zone")
async def get_catastro_parcels_by_zone(
    cod_zona: str = Query(..., description="Zone code (12 digits urban, 9 digits rural)")
):
    """
    Get all parcels in a specific zone using GetParcelsByZoning stored query.
    """
    try:
        # Use the GetParcelsByZoning stored query
        response = requests.get(
            CATASTRO_WFS_URL,
            params={
                'service': 'wfs',
                'version': '2',
                'request': 'getfeature',
                'STOREDQUERIE_ID': 'GetParcelsByZoning',
                'cod_zona': cod_zona,
                'srsname': 'EPSG::25830'
            },
            verify=False
        )

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Catastro WFS request failed: {response.status_code}")

        # Process GML into GeoJSON
        geojson_data = gml_to_geojson_lite(response.content)
        return geojson_data

    except Exception as e:
        print(f"Server error during parcels by zone query: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying parcels by zone: {e}")


@app.get("/api/catastro-neighbors")
async def get_catastro_neighbors(
    refcat: str = Query(..., description="14-digit cadastral reference (e.g., 3662001TF3136S)")
):
    """
    Get a parcel and its neighboring parcels using GetNeighbourParcel stored query.
    """
    try:
        # Use the GetNeighbourParcel stored query
        response = requests.get(
            CATASTRO_WFS_URL,
            params={
                'service': 'wfs',
                'version': '2',
                'request': 'getfeature',
                'STOREDQUERIE_ID': 'GetNeighbourParcel',
                'refcat': refcat,
                'srsname': 'EPSG::25830'
            },
            verify=False
        )

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Catastro WFS request failed: {response.status_code}")

        # Process GML into GeoJSON
        geojson_data = gml_to_geojson_lite(response.content)
        return geojson_data

    except Exception as e:
        print(f"Server error during neighbors query: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying neighbors: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "service": "cadastre-gateway"}

if __name__ == "__main__":
    import uvicorn
    # Use environment variable for port (required by Railway)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
