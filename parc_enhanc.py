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

#load plain data
data_path = 'C:/Users/Xenerios/Desktop/zan_31/V2/data_sampled'

filename = []
for data in glob.glob(os.path.join(
    data_path, '*.geojson')):

    filename.append(data)
filename

parcels = gpd.read_file(filename[2]).to_crs(2154)

#only retrieve urban parcels (FILTER)

#apply constraints (FILTER)

#area and shape
parcels['area'] = parcels.area.astype(int)

#shapes
parcels = zan31.geom_index(parcels) 
parcels

#compute IDU
parcels['IDU'] = parcels['CODE_DEP']+parcels['CODE_COM']+parcels['SECTION']+parcels['NUMERO']#create unique ID
parcels

#retrieve parcels according to size and geometry index (FILTER)

#urban intensity

#distance - accessibility
parcels_cent = parcels.centroid#returns geoseries

parcels_cent = pd.concat([parcels.reset_index(drop = True), 
                          parcels_cent], 
                          axis = 1
                          )

parcels_cent = parcels_cent.set_geometry(parcels_cent.columns[-1])
parcels_cent = parcels_cent.rename_geometry('geom_cent')
#parcels_cent = parcels_cent.drop(parcels_cent.columns[-3])
parcels_cent.geometry.name#must be centroids column
parcels_cent.geom_type.unique()#must be centroids

parcels_cent

bus = gpd.read_file(filename[1]).to_crs(2154)
bus.geom_type.unique()#must be centroids
bus.name = 'BUS'#always

train = gpd.read_file(filename[3]).to_crs(2154)
train.geom_type.unique()#must be centroids
train.name = 'TRAIN'#always

roads = gpd.read_file(filename[0]).to_crs(2154)
roads
#roads = roads[roads['NATURE']=='Bretelle']#none for haut
roads = roads.buffer(150).unary_union
roads
roads = gpd.GeoDataFrame(geometry=gpd.GeoSeries(roads),
                         crs=2154)
roads
roads = roads.explode()
roads = roads.reset_index()
roads = roads[roads.disjoint(train.unary_union)].centroid
roads
roads.name = 'ROADS'#always

parcels = zan31.ckdtree_nearest(parcels_cent, bus)
parcels

parcels = zan31.ckdtree_nearest(parcels_cent, roads)
parcels

parcels = zan31.ckdtree_nearest(parcels_cent, train)
parcels.columns
dem = gdal.Open(os.path.join(
    data_path, 'dem_haut.tif'))

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

slope_path = 'C:/Users/Xenerios/Desktop/zan_31/V2/data_sampled/slope_haut.tif'

gdal.DEMProcessing(slope_path, 
                   dem_f, 
                   "slope", 
                   computeEdges=True)

##compute slope mean for each parcel
slope = gdal.Open(
    'C:/Users/Xenerios/Desktop/zan_31/V2/data_sampled/slope_haut.tif'
    )

###compute slope_mean using rasterstats
start = time.time()
slope_st = zonal_stats(vectors = parcels['geometry'],
                       raster = slope_path,
                       stats = 'mean'
                       )
end = time.time()
print(end-start)

parcels['slope_mean'] = gpd.GeoDataFrame(slope_st)['mean'].astype(int)

#building's properties (bdnb)

#environmental second class risks






