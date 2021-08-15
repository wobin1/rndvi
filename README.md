# How to generate NDVI

Send a json post request with your aoi in the form body to this ip: 3.8.127.168

You can use the geojson data below to test it:

    {
    "type": "FeatureCollection",
    "name": "aoi",
    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
    "features": [
    { "type": "Feature", "properties": { }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 129.974244252923768, -19.523177489165608 ], [ 129.905918021038701, -19.522558599253745 ], [ 129.907490545070743, -19.619964712749148 ], [ 129.98355884256685, -19.619078208042723 ], [ 129.974244252923768, -19.523177489165608 ] ] ] } }
    ]
    }

Your NDVI will be generated and you will get a download link.

If your aoi is avaible in our database you will get a link in json format to download your ndvi. If the aoi is not available, it will be saved in our database.    You will need to fill our contact form, so that we can send your NDVI download link to you when it's ready. The contact form accepts a json with the following fields:

    full_name
    email
    phone
