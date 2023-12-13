#functions script prior to parc_enhanced
import geopandas as gpd 
import pandas as pd
import numpy as np

from osgeo import gdal
from rasterstats import zonal_stats

from math import pi
import scipy
from scipy.spatial import cKDTree

def geom_index(gdf):

    gdf['miller_index'] = (4*pi*gdf.area)/pow(gdf.length,2)
    gdf['solidity_index'] = gdf.area/gdf.convex_hull.area
    gdf['geom_index'] = (gdf['miller_index']+gdf['solidity_index'])/2
    gdf['par_area'] = gdf.area
    
    return gdf

def ckdtree_nearest(gdf1, gdf2):

    """
    Using kernel density estimation method, 
    return all distances of the nearest neighbor 
    in gdf2 from each point in gdf1.

    parameters
    ----------
    gdf1 = input gdf where to compute distances to nearest neighbor for each point
    gdf2 = input gdf where distances to nearest neighbor are computed with

    warning : geometries must be set to centroids
    """
    #retrieve geometries of each row in a numpy array
    nA = np.array(list(gdf1.geometry.apply(lambda x: (x.x, x.y))))
    nb = np.array(list(gdf2.geometry.apply(lambda x: (x.x, x.y))))

    #use kernel density tree method of scipy 
    btree = cKDTree(nb)#on geometries from gdf2 where nearest neighbors are computed
    dist, idx = btree.query(nA, k=1)#on geometries from gdf1 where distances are computed 
    #regarding nearest neighbors from gdf2

    #include computed data to gdf
    #gdf2_nearest = gdf2.iloc[idx].drop(columns="geometry").reset_index(drop=True)

    gdf = pd.concat(
        [
            gdf1.reset_index(drop=True),
            #gdf2_nearest,
            pd.Series(dist, name = ('dist_{}'.format(gdf2.name)))
        ],
        axis=1)

    return gdf 
    
    def intersect_using_spatial_index(source_gdf, intersecting_gdf):
        """
        Conduct spatial intersection using spatial index for candidates GeoDataFrame to make queries faster.
        Note, with this function, you can have multiple Polygons in the 'intersecting_gdf' and it will return all the points 
        intersect with ANY of those geometries.
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


def urban_intensity(couche_parcelle, couche_bati, IDU, aire_min):
    
    
    #intersection des parcelle sur les batiments (recup IDU pour chaque batiment)
    df_overlay = couche_bati.overlay(couche_parcelle, how='intersection')

    #Suppr morceau de bati dû à un mauvais callage
    df_overlay_clear = df_overlay[df_overlay.area > 50]

    #calcul champ de surfance en entier
    df_overlay_clear['area_bati']= df_overlay_clear.area.astype(int)
    parcelle['area']= parcelle.area.astype(int)

    #regroupement du result par parcelle geom plus area(sum)
    dfjoin = df_overlay_clear.dissolve(IDU ,aggfunc={"area_bati": "sum"})
    dfjoin = dfjoin.reset_index()

    #regroup les polygones batiments par parcelles 
    #jointure du résultat de la surface bati par parcelle aux parcelles
    parcelle_ratio = parcelle.merge(dfjoin[['area_bati', IDU]],how='left', on = IDU)

    #Calcul du pourcentage final
    parcelle_ratio['urb_inten_pourcent'] = parcelle_ratio['area_bati']/parcelle_ratio['area']*100
    #remplir les nodata en 0%(pas de batiment sur la parcelle)
    parcelle_ratio['urb_inten_pourcent'] = parcelle_ratio['urb_inten_pourcent'].fillna(0)
    
    #divisiblity
    
    dfjoin['geometry'] = dfjoin['geometry'].convex_hull.buffer(20)
    dfjoin = dfjoin.rename(columns={IDU: f'B_{IDU}'})
    #intersection du buffer avec les parcelles
    dfjoin_clear = dfjoin.overlay(parcelle_ratio,how='intersection')
    #Check IDU compatibility 
    dfjoin_clear = dfjoin_clear[dfjoin_clear[f'B_{IDU}']==dfjoin_clear[IDU]]
    
    parcelle_divisible = parcelle_ratio.overlay(dfjoin_clear, how='difference')
    parcelle_divisible['area_div'] = parcelle_divisible.area.astype(int)

    parcelle_ratio = parcelle.merge(parcelle_divisible[[IDU, 'area_div']],how='left', on = IDU)
    parcelle_ratio = parcelle_ratio.reset_index()
    parcelle_ratio['divisible'] = parcelle_ratio['area_div'].apply(lambda x: 1 if x > aire_min else 0)
    
    return parcelle_ratio, parcelle_divisible

def maximiser (df,list_col):
    '''
    Transformation des critères minimisé en critère maximiser 
    EXP : dist aux gares plus petites valeurs = plus importantes valeurs
    ------
    df =  geodataframe contenant les critères 
    list_col = liste des colonnes à maximiser
    '''
    for i in range (len(list_col)):
        df['max_{}'.format(list_col[i])] = df[list_col[i]].max()-df[list_col[i]]
    return df

def norma_sum (df,sum_critere,list_col):
    '''
    Transformation des critères en critère normalisé
    méthode x = col_x/Sum de la ligne
    ------
    df =  geodataframe contenant les critères
    sum_critere = colonne de sum par ligne des colonnes de critère
    list_col = liste des colonnes à normaliser
    '''
    for i in range (len(list_col)):
        df['norm_{}'.format(list_col[i])]=df[list_col[i]]/df[sum_critere]
    return df
