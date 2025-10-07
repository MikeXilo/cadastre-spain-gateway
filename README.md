# Spanish Cadastre Gateway Service

A FastAPI microservice that provides access to Spanish Cadastre (Catastro) data through the official WFS (Web Feature Service) API. This service acts as a secure gateway, handling coordinate transformations and converting GML responses to GeoJSON format.

## 🏗️ Architecture

This service bridges the gap between modern web applications and the Spanish Cadastre's OGC-compliant WFS service:

- **Input**: WGS84 bounding boxes (standard web coordinates)
- **Processing**: Coordinate transformation to ETRS89 UTM Zone 30
- **Output**: GeoJSON cadastral parcel data
- **Deployment**: Railway cloud platform

## 🚀 Features

- ✅ **Real-time Spanish Cadastre data** from official WFS
- ✅ **Automatic coordinate transformation** (WGS84 ↔ ETRS89 UTM Zone 30)
- ✅ **GML to GeoJSON conversion** for web compatibility
- ✅ **CORS-enabled** for frontend integration
- ✅ **Production-ready** with proper error handling
- ✅ **Docker support** for containerized deployment

## 📊 Data Coverage

- **Coverage**: 95% of Spanish territory (excluding Basque Country and Navarra)
- **Resolution**: 1:1000 for urban areas, 1:5000 for rural areas
- **Update Frequency**: Real-time data from official Cadastre database
- **Data Types**: Cadastral parcels with precise geometry and properties

## 🛠️ Technical Stack

- **Framework**: FastAPI (Python 3.11+)
- **Coordinate System**: ETRS89 UTM Zone 30 (EPSG:25830)
- **Dependencies**: 
  - `pyproj` for coordinate transformations
  - `owslib` for WFS communication
  - `lxml` for XML/GML parsing
  - `geojson` for output formatting

## 📡 API Endpoints

### GET `/api/catastro-plots`

Retrieves cadastral parcel data for a given bounding box.

**Parameters:**
- `bbox` (required): Bounding box in WGS84 format `minLon,minLat,maxLon,maxLat`

**Example:**
```
GET /api/catastro-plots?bbox=-3.7038,40.4168,-3.6948,40.4258
```

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lon1, lat1], [lon2, lat2], ...]]
      },
      "properties": {
        "cadastral_id": "unique_parcel_identifier"
      }
    }
  ]
}
```

### GET `/health`

Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "cadastre-gateway"
}
```

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/MikeXilo/cadastre-spain-gateway.git
   cd cadastre-spain-gateway
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the service**
   ```bash
   python main.py
   ```

4. **Test the endpoint**
   ```bash
   curl "http://localhost:8000/api/catastro-plots?bbox=-3.7038,40.4168,-3.6948,40.4258"
   ```

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t cadastre-spain-gateway .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 cadastre-spain-gateway
   ```

## 🌐 Production Deployment

### Railway Deployment

1. **Connect GitHub repository** to Railway
2. **Railway auto-detects** Python service
3. **Deploy automatically** on git push
4. **Environment variables** configured automatically

### Environment Variables

- `PORT`: Server port (Railway sets this automatically)
- No additional configuration required

## 📍 Usage Examples

### Madrid (1km x 1km area)
```
GET /api/catastro-plots?bbox=-3.7038,40.4168,-3.6948,40.4258
```

### Barcelona
```
GET /api/catastro-plots?bbox=2.1734,41.3851,2.1824,41.3941
```

### Seville
```
GET /api/catastro-plots?bbox=-5.9845,37.3891,-5.9755,37.3981
```

## 🔧 Configuration

### Coordinate Systems
- **Input**: WGS84 (EPSG:4326) - standard web coordinates
- **WFS Query**: ETRS89 UTM Zone 30 (EPSG:25830) - Spanish Cadastre standard
- **Output**: WGS84 (EPSG:4326) - GeoJSON standard

### WFS Parameters
- **Service**: Spanish Cadastre WFS (https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx)
- **Version**: WFS 2.0.0
- **Feature Type**: `cp.cadastralparcel`
- **Output Format**: GML 3.2

## 🚨 Limitations

- **Area Size**: Maximum 1km² per request (WFS limitation)
- **Feature Limit**: Maximum 5,000 parcels per request
- **Coverage**: 95% of Spanish territory
- **Rate Limiting**: Respects Spanish Cadastre service limits

## 🐛 Troubleshooting

### Common Issues

1. **"No records founded for BBOX"**
   - Try a smaller bounding box
   - Ensure coordinates are within Spain

2. **"Area of extension out of limits"**
   - Reduce the bounding box size
   - Maximum 1km² recommended

3. **Coordinate transformation errors**
   - Ensure `pyproj` is properly installed
   - Check that coordinates are valid WGS84

## 📚 Technical Details

### WFS Integration
This service communicates with the Spanish Cadastre WFS using:
- **GetFeature requests** with bounding box filters
- **ETRS89 UTM Zone 30** coordinate system
- **GML 3.2** response parsing
- **Exception handling** for WFS errors

### Coordinate Transformation
- **Input**: WGS84 (longitude, latitude)
- **Transform**: Using `pyproj` for accurate conversion
- **WFS Query**: ETRS89 UTM Zone 30 (easting, northing)
- **Output**: Back to WGS84 for GeoJSON compatibility

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Services

- **Spanish Cadastre WFS**: https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx
- **INSPIRE Directive**: European spatial data infrastructure
- **OGC Standards**: Open Geospatial Consortium specifications

## 📞 Support

For issues and questions:
- **GitHub Issues**: Create an issue in this repository
- **Documentation**: Spanish Cadastre official documentation
- **WFS Standards**: OGC Web Feature Service 2.0.0 specification

---

**Built with ❤️ for Spanish geospatial data access**
