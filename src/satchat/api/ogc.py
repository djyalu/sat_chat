"""OGC (WMS/WCS) services for BYOC satellite data visualization"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import io
import base64

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
import aiohttp

from satchat.core.database import get_async_db
from satchat.models.database import User
from satchat.api.auth import get_current_active_user
from satchat.services.satellite.sentinel_hub import SentinelHubService
from satchat.core.config import settings

router = APIRouter()


@router.get("/wms/capabilities")
async def get_wms_capabilities(
    current_user: User = Depends(get_current_active_user)
) -> Response:
    """Get WMS GetCapabilities document for BYOC collection"""
    
    service = SentinelHubService()
    
    # WMS GetCapabilities XML template for BYOC collection
    capabilities_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms">
    <Service>
        <Name>WMS</Name>
        <Title>SatChat BYOC Marine Debris Monitoring</Title>
        <Abstract>WMS service for Korea Sea marine debris monitoring data</Abstract>
        <KeywordList>
            <Keyword>Marine Debris</Keyword>
            <Keyword>Korea Sea</Keyword>
            <Keyword>Sentinel Hub</Keyword>
            <Keyword>BYOC</Keyword>
        </KeywordList>
        <OnlineResource xlink:href="https://services.sentinel-hub.com/ogc/wms/{settings.sentinel_hub_instance_id}"/>
        <ContactInformation>
            <ContactPersonPrimary>
                <ContactPerson>Telefix</ContactPerson>
                <ContactOrganization>Telefix</ContactOrganization>
            </ContactPersonPrimary>
            <ContactElectronicMailAddress>go41@naver.com</ContactElectronicMailAddress>
        </ContactInformation>
    </Service>
    
    <Capability>
        <Request>
            <GetCapabilities>
                <Format>text/xml</Format>
            </GetCapabilities>
            <GetMap>
                <Format>image/png</Format>
                <Format>image/jpeg</Format>
                <Format>image/tiff</Format>
            </GetMap>
        </Request>
        
        <Layer>
            <Name>KOREA_SEA_DEBRIS</Name>
            <Title>Korea Sea Marine Debris</Title>
            <Abstract>Marine debris detection data from multiple satellite sources</Abstract>
            <CRS>EPSG:4326</CRS>
            <CRS>EPSG:3857</CRS>
            <EX_GeographicBoundingBox>
                <westBoundLongitude>124.0</westBoundLongitude>
                <eastBoundLongitude>132.0</eastBoundLongitude>
                <southBoundLatitude>32.0</southBoundLatitude>
                <northBoundLatitude>39.0</northBoundLatitude>
            </EX_GeographicBoundingBox>
            
            <Layer queryable="1">
                <Name>BYOC_{settings.byoc_collection_id}</Name>
                <Title>Korea Sea BYOC Collection</Title>
                <Style>
                    <Name>default</Name>
                    <Title>Default visualization</Title>
                </Style>
                <Style>
                    <Name>debris_highlight</Name>
                    <Title>Debris highlighting</Title>
                </Style>
                <Style>
                    <Name>indices</Name>
                    <Title>Spectral indices</Title>
                </Style>
            </Layer>
        </Layer>
    </Capability>
</WMS_Capabilities>"""
    
    return Response(
        content=capabilities_xml,
        media_type="text/xml",
        headers={"Content-Type": "text/xml; charset=utf-8"}
    )


@router.get("/wms/map")
async def get_wms_map(
    layers: str = Query(..., description="Layer name"),
    bbox: str = Query(..., description="Bounding box (minx,miny,maxx,maxy)"),
    width: int = Query(512, ge=256, le=2048),
    height: int = Query(512, ge=256, le=2048),
    format: str = Query("image/png", description="Output format"),
    time: Optional[str] = Query(None, description="Time range"),
    style: str = Query("default", description="Visualization style"),
    current_user: User = Depends(get_current_active_user)
) -> StreamingResponse:
    """WMS GetMap request for BYOC visualization"""
    
    service = SentinelHubService()
    
    # Parse bbox
    bbox_values = [float(x) for x in bbox.split(',')]
    if len(bbox_values) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bbox format"
        )
    
    # Create evalscript based on style
    if style == "debris_highlight":
        evalscript = service.create_marine_debris_evalscript()
    elif style == "indices":
        evalscript = create_indices_evalscript()
    else:
        evalscript = create_default_evalscript()
    
    # Prepare Process API request
    process_request = {
        "input": {
            "bounds": {
                "bbox": bbox_values,
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                }
            },
            "data": [{
                "type": f"byoc-{settings.byoc_collection_id}",
                "dataFilter": {}
            }]
        },
        "output": {
            "width": width,
            "height": height,
            "responses": [{
                "identifier": "default",
                "format": {
                    "type": format
                }
            }]
        },
        "evalscript": evalscript
    }
    
    # Add time filter if provided
    if time:
        process_request["input"]["data"][0]["dataFilter"]["timeRange"] = {
            "from": time.split("/")[0] if "/" in time else time,
            "to": time.split("/")[1] if "/" in time else datetime.utcnow().isoformat()
        }
    
    # Get access token
    token = await service.get_access_token()
    
    # Make Process API request
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{service.process_url}/process",
            json=process_request,
            headers=headers
        ) as response:
            if response.status == 200:
                content = await response.read()
                return StreamingResponse(
                    io.BytesIO(content),
                    media_type=format,
                    headers={
                        "Content-Type": format,
                        "Cache-Control": "public, max-age=3600"
                    }
                )
            else:
                error = await response.text()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Process API error: {error}"
                )


@router.get("/wcs/capabilities")
async def get_wcs_capabilities(
    current_user: User = Depends(get_current_active_user)
) -> Response:
    """Get WCS GetCapabilities document for BYOC collection"""
    
    capabilities_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<wcs:Capabilities version="2.0.1" 
    xmlns:wcs="http://www.opengis.net/wcs/2.0"
    xmlns:gml="http://www.opengis.net/gml/3.2"
    xmlns:xlink="http://www.w3.org/1999/xlink">
    
    <ows:ServiceIdentification xmlns:ows="http://www.opengis.net/ows/2.0">
        <ows:Title>SatChat BYOC Coverage Service</ows:Title>
        <ows:Abstract>WCS service for Korea Sea marine debris monitoring data</ows:Abstract>
        <ows:Keywords>
            <ows:Keyword>Marine Debris</ows:Keyword>
            <ows:Keyword>Coverage</ows:Keyword>
            <ows:Keyword>BYOC</ows:Keyword>
        </ows:Keywords>
        <ows:ServiceType>WCS</ows:ServiceType>
        <ows:ServiceTypeVersion>2.0.1</ows:ServiceTypeVersion>
    </ows:ServiceIdentification>
    
    <ows:ServiceProvider xmlns:ows="http://www.opengis.net/ows/2.0">
        <ows:ProviderName>Telefix</ows:ProviderName>
        <ows:ServiceContact>
            <ows:ContactInfo>
                <ows:Address>
                    <ows:ElectronicMailAddress>go41@naver.com</ows:ElectronicMailAddress>
                </ows:Address>
            </ows:ContactInfo>
        </ows:ServiceContact>
    </ows:ServiceProvider>
    
    <wcs:Contents>
        <wcs:CoverageSummary>
            <wcs:CoverageId>BYOC_{settings.byoc_collection_id}</wcs:CoverageId>
            <wcs:CoverageSubtype>RectifiedGridCoverage</wcs:CoverageSubtype>
            <ows:BoundingBox xmlns:ows="http://www.opengis.net/ows/2.0">
                <ows:LowerCorner>124.0 32.0</ows:LowerCorner>
                <ows:UpperCorner>132.0 39.0</ows:UpperCorner>
            </ows:BoundingBox>
        </wcs:CoverageSummary>
    </wcs:Contents>
</wcs:Capabilities>"""
    
    return Response(
        content=capabilities_xml,
        media_type="text/xml",
        headers={"Content-Type": "text/xml; charset=utf-8"}
    )


@router.get("/wcs/coverage")
async def get_wcs_coverage(
    coverage_id: str = Query(..., description="Coverage ID"),
    bbox: str = Query(..., description="Bounding box"),
    format: str = Query("image/tiff", description="Output format"),
    width: int = Query(512, ge=256, le=2048),
    height: int = Query(512, ge=256, le=2048),
    time: Optional[str] = Query(None, description="Time slice"),
    current_user: User = Depends(get_current_active_user)
) -> StreamingResponse:
    """WCS GetCoverage request for raw data access"""
    
    service = SentinelHubService()
    
    # Parse bbox
    bbox_values = [float(x) for x in bbox.split(',')]
    
    # Create evalscript for raw data
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: ["B01", "B02", "B03", "B04", "dataMask"],
            output: {
                bands: 4,
                sampleType: "UINT16"
            }
        };
    }
    
    function evaluatePixel(sample) {
        return [sample.B01 * 10000, 
                sample.B02 * 10000, 
                sample.B03 * 10000, 
                sample.B04 * 10000];
    }
    """
    
    # Prepare Process API request
    process_request = {
        "input": {
            "bounds": {
                "bbox": bbox_values,
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                }
            },
            "data": [{
                "type": f"byoc-{settings.byoc_collection_id}",
                "dataFilter": {}
            }]
        },
        "output": {
            "width": width,
            "height": height,
            "responses": [{
                "identifier": "default",
                "format": {
                    "type": format
                }
            }]
        },
        "evalscript": evalscript
    }
    
    # Add time filter
    if time:
        process_request["input"]["data"][0]["dataFilter"]["timeRange"] = {
            "from": time,
            "to": time
        }
    
    # Get access token
    token = await service.get_access_token()
    
    # Make request
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{service.process_url}/process",
            json=process_request,
            headers=headers
        ) as response:
            if response.status == 200:
                content = await response.read()
                return StreamingResponse(
                    io.BytesIO(content),
                    media_type=format,
                    headers={
                        "Content-Type": format,
                        "Content-Disposition": f"attachment; filename=coverage_{coverage_id}.tif"
                    }
                )
            else:
                error = await response.text()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Coverage request failed: {error}"
                )


@router.get("/wmts/capabilities")
async def get_wmts_capabilities(
    current_user: User = Depends(get_current_active_user)
) -> Response:
    """Get WMTS capabilities for tiled map service"""
    
    capabilities_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Capabilities version="1.0.0" xmlns="http://www.opengis.net/wmts/1.0">
    <ServiceIdentification>
        <Title>SatChat WMTS Service</Title>
        <Abstract>Web Map Tile Service for Korea Sea monitoring</Abstract>
    </ServiceIdentification>
    
    <Contents>
        <Layer>
            <Title>Korea Sea Marine Debris</Title>
            <Identifier>BYOC_{settings.byoc_collection_id}</Identifier>
            <Style isDefault="true">
                <Identifier>default</Identifier>
            </Style>
            <Format>image/png</Format>
            <TileMatrixSetLink>
                <TileMatrixSet>EPSG:3857</TileMatrixSet>
            </TileMatrixSetLink>
            <ResourceURL format="image/png" 
                template="https://services.sentinel-hub.com/ogc/wmts/{settings.sentinel_hub_instance_id}/{{TileMatrix}}/{{TileCol}}/{{TileRow}}.png"/>
        </Layer>
        
        <TileMatrixSet>
            <Identifier>EPSG:3857</Identifier>
            <SupportedCRS>urn:ogc:def:crs:EPSG::3857</SupportedCRS>
        </TileMatrixSet>
    </Contents>
</Capabilities>"""
    
    return Response(
        content=capabilities_xml,
        media_type="text/xml"
    )


def create_default_evalscript() -> str:
    """Create default visualization evalscript"""
    return """
    //VERSION=3
    function setup() {
        return {
            input: ["B03", "B02", "B01", "dataMask"],
            output: {
                bands: 4,
                sampleType: "AUTO"
            }
        };
    }
    
    function evaluatePixel(sample) {
        return [sample.B03 * 2.5,
                sample.B02 * 2.5,
                sample.B01 * 2.5,
                sample.dataMask];
    }
    """


def create_indices_evalscript() -> str:
    """Create spectral indices visualization evalscript"""
    return """
    //VERSION=3
    function setup() {
        return {
            input: ["B02", "B03", "B04", "B08", "dataMask"],
            output: {
                bands: 4,
                sampleType: "AUTO"
            }
        };
    }
    
    function evaluatePixel(sample) {
        // Calculate indices
        let NDVI = (sample.B08 - sample.B04) / (sample.B08 + sample.B04 + 0.001);
        let NDWI = (sample.B03 - sample.B08) / (sample.B03 + sample.B08 + 0.001);
        let FAI = sample.B08 - (sample.B04 + (sample.B04 - sample.B03));
        
        // Visualize as RGB
        return [FAI * 10 + 0.5,
                NDVI + 0.5,
                NDWI + 0.5,
                sample.dataMask];
    }
    """