# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 11:01:47 2023

@authors: M.Joffrion, M.Echevarria, T.Mervant

Objet : Création d'une tâche urbaine simple ou jointe aux géométries parcellaires

Données d'entrée : 
    *bati_topo = IGN BD TOPO (couche bâtiment à l'échelle départementale)
    *parcelle = IGN BD PARCELLAIRE (si jointure aux géométries parcellaires envisagée)
    *ROI = epci_auterivain.geojson (délimitation zone d'étude Admin EXPRESS IGN)
    
Output : 
    *TU_bd_topo.gpkg = TU (Tâche Urbaine)


# installation des librairies rtree et GeoPandas
!pip install rtree 
# GeoPandas
!pip install geopandas
"""

import geopandas as gpd
import pandas as pd


 # In[] Fonctions

def intersect_using_spatial_index(source_gdf, intersecting_gdf):
    """
    Conduct spatial intersection using spatial index for candidates GeoDataFrame to make queries faster.
    Note, with this function, you can have multiple Polygons in the 'intersecting_gdf' 
    and it will return all the points intersect with ANY of those geometries.
    
    parameters
    ----------
    source_gdf : input gdf to intersect
    intersecting_gdf : input gdf to intersect with
    """
    source_sindex = source_gdf.sindex
    possible_matches_index = []
    
    # 'itertuples()' function is a faster version of 'iterrows()'
    for other in intersecting_gdf.itertuples():
        bounds = other.geometry.bounds
        c = list(source_sindex.intersection(bounds))
        possible_matches_index += c
    
    # Get unique candidates
    unique_candidate_matches = list(set(possible_matches_index))
    possible_matches = source_gdf.iloc[unique_candidate_matches]

    # Conduct the actual intersect
    result = possible_matches.loc[possible_matches.intersects(intersecting_gdf.unary_union)]
    return result

def dilat_erode(gdf2erode,x_dilate, x_erode):
    """
    Submit input polygons to an erosion / dilatation process

    Parameters
    ----------
    gdf2erode : GeoDataFrame
        Input gdf containing polygons to process.
    x_dilate : INT
        Buffer size (units depending on gdf2erode's CRS - ex 2154 ~ 50meters)
    x_erode : INT
        Buffer size (units depending on gdf2erode's CRS - ex 2154 ~ -50meters)
.

    Returns
    -------
    gdferode : GeoDataFrame
        Output gdf containing cleaned singled out polygons. 

    """
    
    #dilatation x_dilate via buffer
    gdferode = gdf2erode
    gdferode['geometry'] = gdf2erode['geometry'].buffer(x_dilate)

    #erosion x_erode via buffer
    gdferode = gdferode.dissolve()
    gdferode = gdferode.buffer(x_erode)
    
    #séparation des polygones disjoint
    gdferode = gdferode.explode()
    
    return gdferode

def nb_bat_in_tu_ilot (gdf_tu, gdf_bat, gdf_bat_id):
    """
    Get building's sum by polygons

    Parameters
    ----------
    gdf_tu : GeoDataFrame 
        Input gdf containing polygons where building's sum is to be computed.
    gdf_bat : GeoDataFrame
        Input gdf containing buildings to sum.
    gdf_bat_id : String
        buildings' unique id (col name).

    Returns
    -------
    gdf_tu : GeoDataFrame
        gdf_tu enhanced with building's sum as a column ('baticount')

    """
    #create id in gdf_tu 
    gdf_tu['tu_id'] = gdf_tu.index
    
    #spatial join des batiments sur les polygones tu
    dfsjoin = gdf_tu.sjoin(gdf_bat, how='left')
    
    #group by polygones tu en comptant les batiments 
    dfcount = dfsjoin.groupby('tu_id')[gdf_bat_id].count().rename('baticount').reset_index()
    
    #ajout du résultat au gdf_tu
    gdf_tu =  gdf_tu.merge(dfcount[['tu_id','baticount']], on='tu_id')
    
    #nettoyage
    gdf_tu = gdf_tu.drop(columns='tu_id')
    return gdf_tu


 # In[] Ouverture
#ouverture ROI
ROI = gpd.read_file('epci_auterivain.geojson')

#ouverture batiment du ROI
bati_topo = gpd.read_file('bd_topo.gpkg' ,layer='batiment')
bati_topo_roi = intersect_using_spatial_index(bati_topo, ROI)
bati_topo = 0

#ouverture des parcelles du ROI
parcelle = gpd.read_file('PARCELLE.shp' )
parcelle_roi = intersect_using_spatial_index(parcelle, ROI)
parcelle = 0

 # In[] Calcul de la TU

#dilatation 50m via buffer
TU_topo = dilat_erode(bati_topo_roi, 50, -50)

TU_topo1 = TU_topo
#création d'un GPD 
TU_topo1 = gpd.GeoDataFrame(geometry=gpd.GeoSeries(TU_topo1))

#comptage du nombre de batiment par polygone pour filtrer les ilots par nbr de bati
TU_topo1 = nb_bat_in_tu_ilot(TU_topo1, bati_topo_roi, 'cleabs')

#création champ 'type_zone' U 
TU_topo1['type_zone'] = 'U'
#plot de la TU brute
TU_topo1.plot()

 # In[] phase de filtre sur Area et Nombre de batiment par îlots
 
#suppr les résidus géométriques < 5000m2 critère de filtre à définir

TU_topo1 = TU_topo1[TU_topo1.area > 5000]

#filtrer les entités geométriques de grande surface mais ne possédant pas suffisament de batiments
#EXP : hameaux ou fermes
 
TU_topo1 = TU_topo1[TU_topo1['baticount'] > 15 ]
                   
 # In[] Jointure du result aux Parcelles
 
#jointure du résultat aux parcelles
parcelle_zone = parcelle_roi.sjoin(TU_topo1, how="left", predicate='intersects')
# remplir les cases vide de type_zone
parcelle_zone['type_zone'] = parcelle_zone['type_zone'].fillna('NAF')



 # In[] Visualisation
import matplotlib.colors as colors

parcelle_zone.plot('type_zone',cmap = colors.ListedColormap( ["lightgreen", "darkred"]))

# In[] Ecriture

TU_topo1.to_file("TU_bd_topo.gpkg",layer='tu_brute', driver="GPKG")
parcelle_zone.to_file("TU_bd_topo.gpkg",layer='parcelle_tu', driver="GPKG")

