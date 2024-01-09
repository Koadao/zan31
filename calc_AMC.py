# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 11:01:47 2023

@authors: M.Joffrion, M.Echevarria, T.Mervant

Objet : compute multiple-criteria analysis based on the parc_enhanced.py output

Input : parcels_rich.gpkg (parc_enhanced output)
    
Output : i_multi_crit.csv (csv file containing IDU and final multiple-criteria )

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
    list_max = []
    for i in range (len(list_col)):
        df[f'max_{list_col[i]}'] = df[list_col[i]].max()-df[list_col[i]]
        list_max.append(f'max_{list_col[i]}')
    return df , list_max

def norma_sum (df,sum_critere,list_col):
    '''
    Transformation des critères en critères normalisés
    méthode x = col_x/Sum de la ligne
    ------
    df =  geodataframe contenant les critères
    sum_critere = colonne de sum par ligne des colonnes de critère
    list_col = liste des colonnes à normaliser
    '''
    list_norma_sum = []
    for i in range (len(list_col)):
        df[f'norm_{list_col[i]}'.format(list_col[i])]=df[list_col[i]]/df[sum_critere]
        list_norma_sum.append(f'norm_{list_col[i]}')
    return df, list_norma_sum


os.chdir('C:/Users/dsii/Documents/zan_31_atelier/data_test')

indice_parcelle =  gpd.read_file('parcels_rich.gpkg')
indice_parcelle = indice_parcelle[['IDU','area','cizi_zone','geom_index', 'ffo_bat_annee_construction','dist_ROADS','dist_TRAIN','dist_BUS','slope_mean','urb_inten_pourcent','class_conso_int_mean','Classe_oso']]

list_col= indice_parcelle.columns

#check na
list_na = []
for i in range(len(list_col)):
     na = indice_parcelle[list_col[i]].isna().sum()
     list_na.append([list_col[i],na])
     
#fill na
indice_parcelle['ffo_bat_annee_construction'] = indice_parcelle['ffo_bat_annee_construction'].fillna(0)
indice_parcelle['Classe_oso'] = indice_parcelle['Classe_oso'].fillna(5)

#initiate list columns 
list_unchanged = ['area','cizi_zone','geom_index','class_conso_int_mean']
list_col_max = ['ffo_bat_annee_construction','dist_ROADS','dist_TRAIN','dist_BUS','slope_mean','urb_inten_pourcent','Classe_oso']


indice_parcelle , list_col_maximiser = maximiser(indice_parcelle,list_col_max)

#gestion des cas annees de construction = 0 transformés en 2020 avec la fonction maximiser
indice_parcelle['max_ffo_bat_annee_construction'] = indice_parcelle['max_ffo_bat_annee_construction'].apply(lambda x: 0 if x == 2020 else x)#become 0 again if false 2020

#Sum par ligne des colonnes de critères
list_col_a_sum = list_unchanged + list_col_maximiser
indice_parcelle['sum_critere'] = 0
for i in range(len(list_col_a_sum)):
    indice_parcelle['sum_critere'] = indice_parcelle['sum_critere'] + indice_parcelle[list_col_a_sum[i]]

#application fonction norma_sum
indice_parcelle, list_col_normalise = norma_sum(indice_parcelle, 'sum_critere',list_col_a_sum)


#create dict of weights
list_poids = [0]*11 #poids vides
dict_w = {list_col_normalise[i]: list_poids[i] for i in range(len(list_col_normalise))}
#définir les poids

#Calcul de la Somme pondérée
indice_parcelle['i_multi_crit'] = 0
for i in range(len(list_col_normalise)):
    indice_parcelle['i_multi_crit'] = indice_parcelle['i_multi_crit'] + indice_parcelle[list_col_normalise[i]]* dict_w[list_col_normalise[i]]
    
#write in csv
indice_parcelle[['IDU','i_multi_crit']].to_csv('i_multi_crit.csv')


