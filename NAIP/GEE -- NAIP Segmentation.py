#!/usr/bin/env python
# coding: utf-8

# ## Load packages and initiate earth engine

# In[1]:


import ee
ee.Initialize()

import folium
import palette
import geemap.eefolium as emap
import subprocess
#import geemap as emap
from IPython.display import Image


# ## Define aoi of NAIP images

# In[2]:


collection = ee.ImageCollection('USDA/NAIP/DOQQ')
aoi = ee.Geometry.Polygon([
    [-74.02,40.90],
          [-74.02,40.85],
          [-73.90,40.85],
          [-73.90,40.90]
])
centroid = aoi.centroid()
long, lat = centroid.getInfo()['coordinates']
print("long = {}, lat = {}".format(long,lat))


# ## Filter NAIP image collection by time and aoi

# In[3]:


long_lat = ee.Geometry.Point(long, lat)
naip = collection.filterBounds(aoi)
naip17 = collection.filterDate('2017-05-01','2017-8-05')
count = naip17.size().getInfo()
print('Count:', count)


# ## Display NAIP images for aoi

# In[4]:


Map = emap.Map(center=[lat,long], zoom=15)

Map.add_basemap('TERRAIN') 
#vis = {'bands': ['N', 'R', 'G']}

vis = {'bands': ['R', 'G', 'B']}
imgs = naip17.mosaic().clip(aoi)
#Map.addLayer(aoi)
Map.addLayer(imgs,vis)
Map


# ## Calculate NDVI

# In[5]:


#nir, r = imgs.select('N'), imgs.select('R')
ndvi = imgs.normalizedDifference(["N", "R"])
ndvi_vis = {'min': -1, 'max': 1, 'palette':['red',  'yellow', 'green']}

#Map.add_basemap('TERRAIN') 
Map.addLayer(ndvi,ndvi_vis)
Map


# ## Show region with NDVI higher than 0.1

# In[6]:


veg_mask = ndvi.updateMask(ndvi.gte(0.1))
veg_vis = {'min': 0, 'max': 1, 'palette': ['blue']}
Map.addLayer(veg_mask,veg_vis)
Map


# ## Images segmentation

# In[7]:


seed = ee.Algorithms.Image.Segmentation.seedGrid(6)
#seg = ee.Algorithms.Image.Segmentation.GMeans(image=imgs,numIterations=100,pValue=50,neighborhoodSize=500)
seg = ee.Algorithms.Image.Segmentation.SNIC(image=imgs, size=10,compactness= 0, neighborhoodSize=500,connectivity= 8, seeds=seed).select(['R_mean', 'G_mean', 'B_mean', 'N_mean', 'clusters'], ['R', 'G', 'B', 'N', 'clusters'])
clusters = seg.select('clusters')


# In[8]:


seg_vis = {'bands': ['R', 'G', 'B'], 'min':0, 'max':1, 'gamma':0.8}
Map.addLayer(clusters.randomVisualizer(), {}, 'clusters',opacity=1)
Map


# ## Calculate per-cluster features (for future use)

# In[9]:


## ndvi
seg_ndvi = ndvi.addBands(clusters).reduceConnectedComponents(ee.Reducer.mean(),'clusters').rename('seg_ndvi')
Map.addLayer(seg_ndvi,{},'seg_ndvi')

## standard-deviation
std = ndvi.addBands(clusters).reduceConnectedComponents(ee.Reducer.stdDev(),'clusters').rename('std')
Map.addLayer(std,{},'StdDev')

## area
area = ee.Image.pixelArea().addBands(clusters).reduceConnectedComponents(ee.Reducer.sum(), 'clusters')
Map.addLayer(area,{}, 'Area')

## perimeter
minMax = clusters.reduceNeighborhood(ee.Reducer.minMax(), ee.Kernel.square(1))
perimeterPixels = minMax.select(0).neq(minMax.select(1)).rename('perimeter')
Map.addLayer(perimeterPixels,{},'perimeterPixels')
perimeter = perimeterPixels.addBands(clusters).reduceConnectedComponents(ee.Reducer.sum(), 'clusters')
Map.addLayer(perimeter, {}, 'Perimeter')

## width and height
sizes = ee.Image.pixelLonLat().addBands(clusters).reduceConnectedComponents(ee.Reducer.minMax(), 'clusters')
width = sizes.select('longitude_max').subtract(sizes.select('longitude_min')).rename('width')
height = sizes.select('latitude_max').subtract(sizes.select('latitude_min')).rename('height')
Map.addLayer(width, {},'Width')
Map.addLayer(height, {}, 'Height')


# ## Filter out objects with NDVI < 0.1

# In[10]:


seg_veg = seg_ndvi.updateMask(seg_ndvi.gte(0.1))

Map2 = emap.Map(center=[lat,long], zoom=15)
Map2.add_basemap('SATELLITE') 
Map2.addLayer(seg_veg.randomVisualizer(), {})
Map2


# ###### Thanks to all the GEE communities and all the code available online. 
