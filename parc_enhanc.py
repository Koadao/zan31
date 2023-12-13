#obj
#enhancement of a dataset of parcels to compute a mutability index

#lib
import sys
import os
import glob

import geopandas as gpd 
import pandas as pd
import numpy as np

from osgeo import gdal
from rasterstats import zonal_stats

from math import pi 
import time

import scipy
from scipy.spatial import cKDTree

import matplotlib.pyplot as plt

sys.path.append('C:/Users/Xenerios/Desktop/zan_31/V2/z31_f')
import zan31

#load data
data_path = 'C:/Users/Xenerios/Desktop/zan_31/V2/data_sampled'

filename = []
for data in glob.glob(os.path.join(
    data_path, '*.geojson')):

    filename.append(data)
filename

parcels = gpd.read_file(filename[1]).to_crs(2154)
parcels_cent = parcels.centroid
parcels_cent.geom_type.unique()

bus = gpd.read_file(filename[0]).to_crs(2154)
bus.geom_type.unique()#must be centroids

train = gpd.read_file(filename[2]).to_crs(2154)
train.geom_type.unique()#must be centroids

roads = gpd.read_file(filename[3]).to_crs(2154)
roads = roads[roads['NATURE']=='Bretelle']#none for haut
roads = roads.buffer(150).unary_union
roads = gpd.GeoDataFrame(geometry=gpd.GeoSeries(roads),
                         crs=roads.crs)
roads = roads.explode()
roads = roads.reset_index()
roads = roads[roads.disjoint(train.unary_union)].centroid

dem = gdal.Open(os.path.join(
    data_path, 'dem_haut.tif'))

parcels

#area (crs must be planar)
parcels['area'] = parcels.length
parcels

#slope data
##clean file (cut + proj)
###set up warp options
warp_options = gdal.WarpOptions(
    format='GTiff',
    dstSRS = 'EPSG:2154',
    cutlineDSName='C:/Users/Xenerios/Desktop/zan_31/V2/data_/roi_haut.shp',
    dstNodata=0, 
)

###apply warp
output_dem = gdal.Warp(
                    'C:/Users/Xenerios/Desktop/zan_31/V2/data_sampled/dem_haut_f.tif', 
                    dem, 
                    options = warp_options
                            )

###declare as None to save memory space
dem = None
output_dem = None

##compute slop
dem_f = gdal.Open(
    'C:/Users/Xenerios/Desktop/zan_31/V2/data_sampled/dem_haut_f.tif'
    )

###get dem properties
geotransform = dem_f.GetGeoTransform()

###load as np.array
dem_array = dem_f.ReadAsArray()

###apply gradient (~space between values)
dz_dx, dz_dy = np.gradient(dem_array, 
                           geotransform[1], 
                           geotransform[5])#pixel size is retrieved

###apply arctan (~trigo algo)
slope_arc = np.arctan(np.sqrt(dz_dx ** 2 + dz_dy ** 2))

###convert radians to degrees
slope_dg = np.degrees(slope_arc)

###new slope tif
driver = gdal.GetDriverByName('GTiff')
slope_dataset = driver.Create(
    'C:/Users/Xenerios/Desktop/zan_31/V2/data_sampled/slope_haut.tif', 
    dem_f.RasterXSize, 
    dem_f.RasterYSize, 
    1, 
    gdal.GDT_Float32)

slope_dataset.SetGeoTransform(geotransform)
slope_dataset.SetProjection(dem_f.GetProjection())

slope_band = slope_dataset.GetRasterBand(1)
slope_band.WriteArray(slope_dg)
slope_band.SetNoDataValue(0)

###declare as None to save memory space
slope_band.FlushCache()
slope_dataset = None
dem_f = None

##compute slope mean for each parcel
slope = gdal.Open(
    'C:/Users/Xenerios/Desktop/zan_31/V2/data_sampled/slope_haut.tif'
    )

slope_path = 'C:/Users/Xenerios/Desktop/zan_31/V2/data_sampled/slope_haut.tif'


###compute slope_mean using rasterstats
slope_st = zonal_stats(vectors = parcels['geometry'],
                       raster = slope_path,
                       stats = 'mean'
                       )

df = pd.DataFrame(slope_st)
df_concat = pd.concat([df, parcels], axis=1)
parcels = gpd.GeoDataFrame(df_concat, 
                           geometry=df_concat.geometry
                           )

parcels_f = gpd.read_file(
     'C:/Users/Xenerios/Desktop/zan_31/V2/data_/parcels_hauter_raw.geojson'
)


start = time.time()
slope_st = zonal_stats(vectors = parcels_f['geometry'],
                       raster = slope_path,
                       stats = 'mean'
                       )
end = time.time()
print(end-start)


#shapes
parcels = zan31.geom_index(parcels) 
parcels

#distance - accessibility

gdf_tr_route2 = gdf_tr_route2[gdf_tr_route2['NATURE']=='Bretelle']
gdf_tr_route2 = gdf_tr_route2.buffer(150).unary_union
gdf_tr_route2 = gpd.GeoDataFrame(geometry=gpd.GeoSeries(gdf_tr_route2), crs=gdf_tr_route.crs)
#erosion dilatation process
gdf_tr_route2 = gdf_tr_route2.explode()
gdf_tr_route2 = gdf_tr_route2.reset_index()
gdf_tr_route_tst = gdf_tr_route2[gdf_tr_route2.disjoint(gdf_gare.unary_union)].centroid
gdf_tr_route_tst.plot()