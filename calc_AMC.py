# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 17:13:38 2023

@author: dsii
"""
import geopandas as gpd
import pandas as pd
import os


def maximiser (df,list_col):
    '''
    Transformation des critères minimisés en critères maximisés
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
    Transformation des critères en critères normalisés
    méthode x = col_x/Sum de la ligne
    ------
    df =  geodataframe contenant les critères
    sum_critere = colonne de sum par ligne des colonnes de critère
    list_col = liste des colonnes à normaliser
    '''
    for i in range (len(list_col)):
        df['norm_{}'.format(list_col[i])]=df[list_col[i]]/df[sum_critere]
    return df

parcels_path = 'C:/Users/Xenerios/Desktop/zan_31/V2/parcelle_indice_multi_critère.gpkg'
indice_parcelle = gpd.read_file('parcelle_indice_multi_critère.gpkg', layer='parcelle_indice_multi_critère')
indice_parcelle.columns

list_col = ['annee_cons','dist_auto_','dist_gare','dist_bus']#data to max 
indice_parcelle['annee_cons'] = indice_parcelle['annee_cons'].fillna(0)
indice_parcelle = maximiser(indice_parcelle,list_col)

#gestion des cas annees de construction = 0 transformés en 2020 avec la fonction maximiser
indice_parcelle['max_annee_cons'] = indice_parcelle['max_annee_cons'].apply(lambda x: 0 if x == 2020 else x)#become 0 again if false 2020


#Sum par ligne des colonnes de critères
indice_parcelle['sum_critere'] = indice_parcelle['IndiceGeom']+indice_parcelle['max_dist_gare']+indice_parcelle['max_dist_bus']+indice_parcelle['max_annee_cons']+indice_parcelle['max_dist_auto_']+indice_parcelle['par_area']

list_col = ['IndiceGeom','max_dist_gare','max_dist_bus','max_annee_cons','max_dist_auto_','par_area']
#application fonction norma_sum
indice_parcelle = norma_sum(indice_parcelle, 'sum_critere',list_col)


#def des poids de chaque critère normalisé w...
w_area = 0.30
w_annee = 0.15
w_dist_gare = 0.15
w_dist_bus = 0.15
w_dist_auto = 0.05
w_geom = 0.20



#Calcul de la Somme pondérée
indice_parcelle['i_mutli_crit']= indice_parcelle['norm_IndiceGeom']*w_geom +indice_parcelle['norm_max_dist_gare']*w_dist_gare +indice_parcelle['norm_max_dist_bus']*w_dist_bus +indice_parcelle['norm_max_annee_cons']*w_annee +indice_parcelle['norm_max_dist_auto_']*w_dist_auto +indice_parcelle['norm_par_area']*w_area

indice_parcelle.to_file('parcelle_indice_multi_critère.gpkg' ,layer='parcelle_AMC')

#function (arg = data, list of unchanged fields, list of fields to max)
#def compute_mce(data, max_fields, unchanged_fields):

