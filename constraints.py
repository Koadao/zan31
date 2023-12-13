#preprocess constraints for parc_enhanced

#lib
import sys
import os
import glob

import geopandas as gpd 
import pandas as pd
import numpy as np

from shapely.ops import unary_union

import time


#load data
##data_path
data_path = 'C:/Users/Xenerios/Desktop/zan_31/V2/constraints'
crs = 2154

##bd topo
start = time.time()
area_of_interest = gpd.read_file(os.path.join(
    data_path,
    'ZONE_D_ACTIVITE_OU_D_INTERET.shp'
)).to_crs(crs)
area_of_interest

cemeteries = gpd.read_file(os.path.join(
    data_path,
    'CIMETIERE.shp'
)).to_crs(crs)
cemeteries

fields = gpd.read_file(os.path.join(
    data_path,
    'TERRAIN_DE_SPORT.shp'
)).to_crs(crs)
fields

train = gpd.read_file(os.path.join(
    data_path,
    'TRONCON_DE_VOIE_FERREE.shp'
)).to_crs(crs)
train

roads = gpd.read_file(os.path.join(
    data_path,
    'TRONCON_DE_ROUTE.shp'
)).to_crs(crs)
roads

print(roads.loc[roads['NATURE']=='Bretelle', 'IMPORTANCE'])

roads_filt = roads[roads['IMPORTANCE']==('1' and '2' and '3' and '4')]
roads_filt

#ppri 
ppri = gpd.read_file(os.path.join(
    data_path, 
    'cv_l_zone_reg_pprn_s_031.shp'
)).to_crs(crs)

ppri['typereg'].unique()

ppri_filt = ppri[ppri['typereg']=='03']
ppri_filt

#cizi
cizi = gpd.read_file(os.path.join(
    data_path, 
    'r_cizi_zi_s_r76.gpkg'
))
cizi

cizi['rf_type'].unique()
cizi_filt = cizi[cizi['rf_type']==('01' and '02')]
cizi_filt

end = time.time()
print(end-start)

#obj : single polygon from all geometries
roi = 'C:/Users/Xenerios/Desktop/zan_31/V2/data_/roi_haut.shp'

##buffer if linear
roads_poly = roads_filt.buffer(2).unary_union
roads_poly#multipolygon -- shapely object

roads_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(roads_poly),
                         crs=crs)#geodataframe
roads_gdf

train_poly = train.buffer(2).unary_union
train_poly#multipolygon -- shapely object

train_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(train_poly),
                         crs=crs)#geodataframe
train_gdf

##explode if multipolygon -- only if geodataframe has been built
roads_gdf = roads_gdf.explode()
roads_gdf

train_gdf = train_gdf.explode()
train_gdf

#extract geom column (only valuable column here) and concat

##unary_union 
train_gdf.GeoSeries
poly_list = [roads_gdf['geometry'], train_gdf['geometry']]

single_polygon = unary_union(poly_list)