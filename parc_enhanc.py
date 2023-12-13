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



parcels = gpd.read_file(filename[1]).to_crs(2154)

#filtre parcels par Tâche urbaine 'U'

#filtre par les contraintes


#calc area
parcels['area'] = parcels.area.astype(int)
#calc i_geom
parcels = zan31.geom_index(parcels) 
#générer l'IDU

#filtre taille minimale et i_geom


#parcelles filtrées


#ouverture bd topo batiment
#calcul de l'intensité urbaine => parcelle bati divisible/ bati pas divisible /sans bati/


#Accésibilité

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
roads = roads.centroid

#roads = roads[roads.disjoint(train.unary_union)].centroid

#calc distance (nearest point )



#Slop calc

dem = gdal.Open(os.path.join(
    data_path, 'dem_haut.tif'))


#clean file (cut + proj)
warp_options = gdal.WarpOptions(
    format='GTiff',
    dstSRS = 'EPSG:2154',
    cutlineDSName='C:/Users/Xenerios/Desktop/zan_31/V2/data_/roi_haut.shp',
    dstNodata=0, 
)
#apply warp
output_dem = gdal.Warp(
                    'C:/Users/Xenerios/Desktop/zan_31/V2/data_sampled/dem_haut_f.tif', 
                    dem, 
                    options = warp_options
                            )

###declare as None to save memory space
dem = None
output_dem = None

slop_path = 'output_slop.tif'

##compute slop
dem_f = gdal.Open(
    'E:/SIGMA/M1/sig/MNT_5M.tif'
    )

gdal.DEMProcessing(slop_path, dem_f, "slope", computeEdges=True)

#compute slope mean for each parcel rasterstats

slope_st = zonal_stats(vectors = parcels['geometry'],
                       raster = slop_path,
                       stats = 'mean'
                       )

parcels['slope_mean'] = gpd.GeoDataFrame(slope_st)['mean'].astype(int)


#Data qualitative BDNB

#jointure de la bndb champs 
#aggrégation ...


#donnée zonages

#ouverture 


 











