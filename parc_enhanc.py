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

import z31_functions
'''
sys.path.append('C:/Users/Xenerios/Desktop/zan_31/V2/z31_f')


#load plain parcels data
##data_path
data_path = 'C:/Users/Xenerios/Desktop/zan_31/V2/data_sampled'

filename = []
for data in glob.glob(os.path.join(
    data_path, '*.geojson')):

    filename.append(data)
filename
'''
os.chdir('C:/Users/dsii/Documents/zan_31_atelier/data_test')

parcels = gpd.read_file('parcelle.geojson')
#only retrieve urban parcels (FILTER)
#open TU

TU_topo = gpd.read_file('TU_topo.gpkg')
parcels = parcels.sjoin(TU_topo, how="left", predicate='intersects')

parcels = parcels[parcels['type_zone']=='U']

parcels = parcels.drop(columns=['index_right','baticount'])
parcels = parcels.reset_index()

#apply constraints (FILTER)
contraint = gpd.read_file('constraints.shp')
#filtre contrainte
ROI = gpd.read_file('epci_auterivain.geojson')

roi = ROI.envelope
contraint = contraint.clip(roi)

start = time.time()
parcels = parcels[parcels.disjoint(contraint.unary_union)]
end = time.time()
print(end-start)

###################
aire_minimum = 500# m2
###################

#area and shape
parcels['area'] = parcels.area.astype(int)
parcels = parcels[parcels['area']>aire_minimum]

#shapes
parcels = z31_functions.geom_index(parcels) 

#compute IDU
#parcels['IDU'] = parcels['CODE_DEP']+parcels['CODE_COM']+parcels['SECTION']+parcels['NUMERO']#create unique ID
new_roi =  parcels.dissolve()
#retrieve parcels according to size and geometry index (FILTER)

start = time.time()

bati_topo = gpd.read_file('bd_topo.gpkg' ,layer='batiment')
bati = z31_functions.intersect_using_spatial_index(bati_topo, new_roi)

end = time.time()
print(end-start)
#urban intensity
#parcels.drop(columns=['index_right','baticount'])

parcels , parcels_div = z31_functions.urban_intensity(parcels , bati, 'IDU',500)

#distance - accessibility
##load and preprocess data
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


bus = gpd.read_file('arrets-du-reseau-lio.geojson').to_crs(2154)
bus.geom_type.unique()#must be centroids
bus.name = 'BUS'#always


gdf_equip_topo = gpd.read_file('bd_topo.gpkg' ,layer='equipement_de_transport')
#aires de repos
aire_de_repos = gdf_equip_topo[gdf_equip_topo['nature']=='Aire de repos ou de service']


train = gdf_equip_topo[gdf_equip_topo['nature']==('Arrêt voyageurs'or
                                         'Gare voyageurs et fret'or
                                         'Gare voyageurs uniquement')
                                         ]

train = train.centroid
train.geom_type.unique()#must be centroids
train.name = 'TRAIN'#always

roads = gpd.read_file('bd_topo.gpkg' ,layer='troncon_de_route').to_crs(2154)
###########selection part
roads = roads[roads['nature']=='Bretelle']#none for haut
roads = roads.buffer(150).unary_union
roads = gpd.GeoDataFrame(geometry=gpd.GeoSeries(roads),
                         crs=2154)
roads = roads.explode()
roads = roads.reset_index()
roads = roads[roads.disjoint(aire_de_repos.unary_union)].centroid
roads.name = 'ROADS'#always


##apply nearest neighbor algorithm
parcels_cent = z31_functions.ckdtree_nearest(parcels_cent, bus)
parcels_cent

parcels_cent = z31_functions.ckdtree_nearest(parcels_cent, roads)
parcels_cent

parcels_cent = z31_functions.ckdtree_nearest(parcels_cent, train)
parcels_cent

##append to original geodataframe
parcels = parcels.merge(parcels_cent[['dist_TRAIN',#change to DIST afterwards 
                                      'dist_BUS', 
                                      'dist_ROADS', 
                                      'IDU']], on = 'IDU')

#####################################################################
###################################################### fin bug ######

#slope data
dem = gdal.Open( 'MNT_BAUTV.tif')

##clean file (cut + proj)
###set up warp options
warp_options = gdal.WarpOptions(
    format='GTiff',
    dstSRS = 'EPSG:2154',
    cutlineDSName='epci_auterivain.geojson',
    dstNodata=0, 
)

###apply warp
output_dem = gdal.Warp(
                    'DEM.tif', 
                    dem, 
                    options = warp_options
                            )

##compute slop
slope_path = 'slope.tif' #output slop_tif
output_slope = gdal.DEMProcessing(slope_path, 
                   output_dem, 
                   "slope", 
                   computeEdges=True)
output_slope = None

###compute slope_mean using rasterstats
start = time.time()
slope_st = zonal_stats(vectors = parcels['geometry'],
                       raster = slope_path,
                       stats = 'mean'
                       )
end = time.time()
print(end-start)

parcels['slope_mean'] = gpd.GeoDataFrame(slope_st)['mean']#.astype(int)
parcels['slope_mean'] = parcels['slope_mean'].fillna(0).astype(int)


#building's properties (bdnb)

#bdnb = gpd.read_file('BDNB_BAUTV.gpkg' ,layer='batiment_groupe_compile')
bdnb = gpd.read_file('BDNB_BAUTV.gpkg' ,layer='batiment_autres_styles_disponible_sur_clic_droit')
#cut Bdnb to ROI
bdnb_cut = z31_functions.intersect_using_spatial_index(bdnb, new_roi)
#sjoin
df_overlay = bdnb_cut.overlay(parcels, how='intersection')
#regroupement du result par parcelle geom plus area(sum)
dfjoin = df_overlay.dissolve('IDU',aggfunc={'ffo_bat_annee_construction': 'min','dpe_class_conso_ener_mean' :'first'})#other aggfunc = first
dfjoin = dfjoin.reset_index()
#merge result selection on IDU
parcels = parcels.merge(dfjoin[['IDU','ffo_bat_annee_construction','dpe_class_conso_ener_mean']],how='left', on='IDU')
#parcels = parcels.reset_index()

parcels['dpe_class_conso_ener_mean'] = parcels['dpe_class_conso_ener_mean'].fillna('N')
#transform class conso in Int
parcels['class_conso_int_mean'] = parcels['dpe_class_conso_ener_mean'].apply(lambda row : ord(row.lower())-96 if row != None and row != '' else row)


#environmental second class risks and land use
oso = gpd.read_file('OSO_BAUTV.shp')
cizi = gpd.read_file('CIZI_BAUTV_03_04.shp')
#filtre cizi si '01','02'

cizi = cizi[cizi['rf_type']!= ('01'and '02')]

parcels = z31_functions.sjoin_1n_maj(parcels, oso, 'Classe')
parcels.rename(columns = {'Classe': 'Classe_oso'}, inplace=True)

parcels = z31_functions.sjoin_1n_maj(parcels, cizi, 'rf_type')
parcels['cizi_zone'] = parcels['rf_type'].fillna('05').astype(int)

parcels = parcels.drop(columns=['index','level_0','fid'])


parcels.to_file('parcels_rich.gpkg')







