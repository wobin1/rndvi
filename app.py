from flask import Flask, request, send_file, redirect, url_for
from flask_mail import Mail, Message
from flask_restful import Api, Resource
import psycopg2
import rasterio
import rasterio.features
import rasterio.warp
import rasterio.mask
from shapely.geometry import shape
import os, glob
import json
import pandas
import geopandas as gpd
import rasterio.crs
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio import plot
import matplotlib.pyplot as plt
from fiona.crs import from_epsg
import numpy as np
import fiona
from osgeo import gdal

app = Flask(__name__)
api = Api(app)
app.config['MAIL_SERVER'] ='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '3d3a99c1d9caa8'
app.config['MAIL_PASSWORD'] = 'c16b2562bd3d89'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)


def getConnection(db_config={}):
    conn = psycopg2.connect(
        host=db_config.get('host', 'localhost'),
        database=db_config.get('db', "rfh_indices_proj"),
        user=db_config.get('user', "postgres"),
        password=db_config.get('password', "password")
    )

    return conn


def insertImageryExtent(values, db_config={}):
    conn = getConnection(db_config)

    query = "INSERT INTO imagery_extents (imagery_extent, imagery_date, "
    query += "imagery_server, imagery_path) VALUES (" + values + ") RETURNING imagery_id"

    cur = conn.cursor()
    cur.execute("ROLLBACK")
    cur.execute(query)
    last_insert_id = cur.fetchone()
    conn.commit()
    cur.close()

    return last_insert_id


def insertImageryBands(values, db_config={}):
    conn = getConnection(db_config)

    query = "INSERT INTO imagery_bands_path (imagery_id, band_name, band_path) VALUES "
    query += values

    cur = conn.cursor()
    cur.execute("ROLLBACK")
    cur.execute(query)
    conn.commit()
    cur.close()

    return True


def extractGeoJsonExtent(img_path):
    with rasterio.open(img_path) as dataset:
        # Read the dataset's valid data mask as a ndarray.
        mask = dataset.dataset_mask()

        # Extract feature shapes and values from the array.
        for geom, val in rasterio.features.shapes(mask, transform=dataset.transform):
            # Transform shapes from the dataset's own coordinate
            # reference system to CRS84 (EPSG:4326).
            geom = rasterio.warp.transform_geom(
                dataset.crs, 'EPSG:4326', geom, precision=6)

            return geom


def indexS2Imagery(img_data={}, config_data={}):
    img_path = img_data.get('img_path', None)
    img_date = img_data.get('img_date', None)
    img_server = img_data.get('img_server', None)
    img_desc = img_data.get('img_desc', '')

    base_path = config_data.get('base_path', None)
    if (img_path is not None and base_path is not None):
        img_bands_path = os.path.join(base_path, img_path)
        img_bands = glob.glob(os.path.join(img_bands_path, "*_B*.jp2"))

        geojson_extent = extractGeoJsonExtent(img_bands[0])

        value = "ST_GeomFromGeoJSON('" + str(
            json.dumps(geojson_extent)) + "'), TO_TIMESTAMP('" + img_date + "', 'YYYY-MM-DD HH:MI:SS'), " + str(
            img_server) + ", '" + img_path + "'"
        id = insertImageryExtent(value)[0]

        band_values = []

        for band in img_bands:
            splits = band.split("_")
            band_name = splits[len(splits) - 1].split(".")[0]
            band_path = splits[len(splits) - 3].split("\\")[1] + "_" + splits[len(splits) - 2] + "_" + splits[
                len(splits) - 1]

            band_values.append("(" + str(id) + ", '" + band_name + "', '" + band_path + "')")

        res = insertImageryBands(",".join(band_values))

        print(res)
    else:
        raise Exception('Invalid values supplied')




def performSearch(aoi, db_config={}):
    conn = getConnection()
    query = "SELECT a.imagery_id, a.imagery_path, b.server_path FROM imagery_extents a INNER JOIN file_servers b ON a.imagery_server = b.server_id "
    query += "WHERE ST_Within(ST_GeomFromGeoJSON('" + str(json.dumps(aoi)) + "'), imagery_extent)"

    cur = conn.cursor()
    cur.execute("ROLLBACK")
    cur.execute(query)
    res = cur.fetchone()
    cur.close()

    return res


def getNDVIBands(img_id, db_config={}):
    conn = getConnection()
    query = "SELECT band_name, band_path FROM imagery_bands_path WHERE imagery_id = " + str(img_id)
    query += " AND band_name IN ('B04', 'B08')"

    cur = conn.cursor()
    cur.execute("ROLLBACK")
    cur.execute(query)
    res = cur.fetchall()
    cur.close()

    bands = {}
    for i in res:
        bands[i[0]] = i[1]

    return bands

def insertMissingAoi(missing_aoi, db_config={}):
    conn = getConnection(db_config)

    query = "INSERT INTO missing_aoi (aoi) VALUES ( '" + str(json.dumps(missing_aoi)) + "') RETURNING aoi_id"

    cur = conn.cursor()
    cur.execute("ROLLBACK")
    cur.execute(query)
    last_insert_id = cur.fetchone()
    conn.commit()
    cur.close()

    return last_insert_id

def insertMissingAoiForm(missing_aoi_form={}, db_config={}):
    conn = getConnection(db_config)
    full_name = missing_aoi_form['full_name']
    email = missing_aoi_form['email']
    phone = missing_aoi_form['phone']


    query = "INSERT INTO missing_aoi (aoi_id, full_name, email, phone) VALUES ('" + str(full_name) + "', '" + str(email) + "', '" + str(phone) + "' )"

    cur = conn.cursor()
    cur.execute("ROLLBACK")
    cur.execute(query)
    conn.commit()
    cur.close()

@app.route('/imagery')
def indexImagery():
    img_data = {
    'img_path': 'S2A_MSIL1C_20210812T013721_N0301_R031_T52KED_20210812T030839.SAFE\GRANULE\L1C_T52KED_A032060_20210812T014008\IMG_DATA',
    'img_server':1,
    'img_date':'2021-08-12 12:18:00'
}

    config_data = {
        'base_path': 'C:/dev/RFH/NDVI/s2'
    }
    indexS2Imagery(img_data, config_data)
    return "done"

class CalculateNdvi(Resource):
    def post(self):
        if request.method == "POST":
            input_data = json.loads(request.data, strict=False)

            geojson = input_data

            aoi = geojson["features"][0]['geometry']
            img_match = performSearch(aoi)
            if img_match:
                band_path = getNDVIBands(img_match[0])
                b04 = os.path.join(img_match[2], img_match[1], band_path['B04'])
                b08 = os.path.join(img_match[2], img_match[1], band_path['B08'])
                b0 = os.path.join(img_match[2], img_match[1])
                features = geojson["features"][0]["geometry"]

                geom = shape(features)
                geom = gpd.GeoDataFrame({'geometry': [geom]})
                geom = geom.set_crs('epsg:4326')
                b04_filename = os.path.splitext(b04)[0]
                b08_filename = os.path.splitext(b08)[0]

                #transform imagery
                # dst_crs = 'EPSG:4326'

                # with rasterio.open(b04) as src:
                #     transform, width, height = calculate_default_transform(
                #         src.crs, dst_crs, src.width, src.height, *src.bounds)
                #     kwargs = src.meta.copy()
                #     kwargs.update({
                #         'crs': dst_crs,
                #         'transform': transform,
                #         'width': width,
                #         'height': height
                #     })

                #     with rasterio.open(b04_filename + '.tif', 'w', **kwargs) as dst:
                #         for i in range(1, src.count + 1):
                #             reproject(
                #                 source=rasterio.band(src, i),
                #                 destination=rasterio.band(dst, i),
                #                 src_transform=src.transform,
                #                 src_crs=src.crs,
                #                 dst_transform=transform,
                #                 dst_crs=dst_crs,
                #                 resampling=Resampling.nearest)

                # with rasterio.open(b08) as src:
                #     transform, width, height = calculate_default_transform(
                #         src.crs, dst_crs, src.width, src.height, *src.bounds)
                #     kwargs = src.meta.copy()
                #     kwargs.update({
                #         'crs': dst_crs,
                #         'transform': transform,
                #         'width': width,
                #         'height': height
                #     })

                # with rasterio.open(b08_filename + '.tif', 'w', **kwargs) as dst:
                #     for i in range(1, src.count + 1):
                #         reproject(
                #             source=rasterio.band(src, i),
                #             destination=rasterio.band(dst, i),
                #             src_transform=src.transform,
                #             src_crs=src.crs,
                #             dst_transform=transform,
                #             dst_crs=dst_crs,
                #             resampling=Resampling.nearest)

                def clipBand4(band4_path):
                    with rasterio.open(band4_path, 'r') as src:
                        out_image, out_transform = rasterio.mask.mask(src, geom["geometry"], crop=True)
                        out_meta = src.meta.copy()
                        out_meta.update({"driver": "GTiff",
                                         "height": out_image.shape[1],
                                         "width": out_image.shape[2],
                                         "transform": out_transform
                                         })
                    with rasterio.open(b0 + "/croppedband4.tiff", "w", **out_meta) as dest:
                        dest.write(out_image)

                def clipBand8(band8_path):
                    with rasterio.open(band8_path, 'r') as src:
                        out_image, out_transform = rasterio.mask.mask(src, geom["geometry"], crop=True)
                        out_meta = src.meta.copy()
                        out_meta.update({"driver": "GTiff",
                                         "height": out_image.shape[1],
                                         "width": out_image.shape[2],
                                         "transform": out_transform
                                         })
                    with rasterio.open(b0 + "/croppedband8.tiff", "w", **out_meta) as dest:
                        dest.write(out_image)

                # clip bands
                clipBand4(b04_filename + '.tif')
                clipBand8(b08_filename + '.tif')

                with rasterio.open(b0 + "/croppedband4.tiff") as dataset:
                    band4 = dataset.read(1).astype('float64')

                with rasterio.open(b0 + "/croppedband8.tiff") as dataset:
                    band8 = dataset.read(1).astype('float64')
                ndvi = (band8 - band4) / (band8 + band4)
                image = rasterio.open(b0 + '/ndvi.tiff', 'w', driver='Gtiff',
                                      width=dataset.width, height=dataset.height,
                                      count=1, crs=dataset.crs,
                                      transform=dataset.transform,
                                      dtype='float64'
                                      )
                image.write(ndvi, 1)
                image.close()
                return {"Download NDVI": 'http://3.8.127.168/download_ndvi'}
            else:
                missing_aoi = geojson
                missing_id = insertMissingAoi(missing_aoi)
                missing_id = missing_id[0]
                aoi_form = 'http://3.8.127.168/contact_form/' + str(missing_id)
                return {"Your aoi is currently not available, "
                        "use the link below to fill our form so that we can contact": aoi_form}


@app.route('/download_ndvi', methods=['get'])
def download_ndvi():

    response = send_file(r'C:\dev\RFH\NDVI\s2\S2A_MSIL1C_20210812T013721_N0301_R031_T52KED_20210812T030839.SAFE\GRANULE\L1C_T52KED_A032060_20210812T014008\IMG_DATA\ndvi.tiff' , mimetype='image/jpeg',
                         attachment_filename='ndvi.tiff',
                         as_attachment=True)
    response.headers["x-filename"] = 'ndvi.tiff'
    response.headers["Access-Control-Expose-Headers"] = 'x-filename'
    return response

@app.route('/contact-form/', methods=['GET','POST'])
def contact_form():
    if request.method == "POST":
        input_data = json.loads(request.data)

        missing_aoi_form = {
            'full_name': input_data['full_name'],
            'email': input_data['email'],
            'phone': input_data['phone']
        }

        msg = Message('aoi', sender='peter@mailtrap.io', recipients=['510aebd243-c27f85@inbox.mailtrap.io'])
        msg.body = "Hey Paul, sending you this email from my Flask app, lmk " \
                   "if it works {}, {}, {}".format(missing_aoi_form['full_name'], missing_aoi_form['email'], missing_aoi_form['phone'] )
        mail.send(msg)

        insertMissingAoiForm(missing_aoi_form)
        return {"message": 'context'}
    return "done"


api.add_resource(CalculateNdvi, "/")
if __name__ == "__main__":
    app.run(host="0.0.0.0", port="80", debug=True)
