# city geojson start
import pandas as pd
import geopandas as gpd
import os
import shapefile
import fiona
import numpy as np
from json import dumps

# merge csv with shapefile
rpop = pd.read_csv('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/2010_place_list_19.csv', sep='\t')
lshape = gpd.read_file('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_place10/tl_2010_19_place10.shp')
rpop.rename(columns={'POP10':'urban_pop'}, inplace=True)
lshape["GEOID10"] = pd.to_numeric(lshape["GEOID10"])
lshape["INTPTLAT10"] = pd.to_numeric(lshape["INTPTLAT10"])
lshape["INTPTLON10"] = pd.to_numeric(lshape["INTPTLON10"])
lshape = lshape.merge(rpop, left_on='GEOID10', right_on="GEOID")
lshape.to_file(os.path.join('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_place10/tl_2010_19_place.shp'))

# reduce attributes
city = gpd.read_file('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_place10/tl_2010_19_place.shp')
city.explode()
city = city.drop(['PLACEFP10','PLACENS10','GEOID10','NAMELSAD10','LSAD10','CLASSFP10','PCICBSA10','PCINECTA10','MTFCC10','FUNCSTAT10','USPS','ANSICODE','NAME','LSAD','FUNCSTAT','HU10','ALAND','AWATER','INTPTLAT','INTPTLONG'], axis = 1)

# save as shapefile
city.to_file(os.path.join('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_place10/tl_2010_place.shp'))

# limit cities to 2500 or larger populations
with fiona.open('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_place10/tl_2010_place.shp') as input:
    meta = input.meta
    with fiona.open('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_place10/2010_place.shp', 'w',**meta) as output:
        for feature in input:
            if feature ['properties']['urban_pop']>=2500:
                output.write(feature)

# convert the shapefile for geojson
reader = shapefile.Reader('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_place10/2010_place.shp','r')
fields = reader.fields[1:]
field_names = [field[0] for field in fields]
buffer = []
for sr in reader.shapeRecords():
       atr = dict(zip(field_names, sr.record))
       geom = sr.shape.__geo_interface__
       buffer.append(dict(type="Feature", \
        geometry=geom, properties=atr))
   
# produce the GeoJSON file
geojson = open('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/city10.geojson', 'w')
geojson.write(dumps({"type": "FeatureCollection",\
"features": buffer}, indent=2) + "\n")
geojson.close()
# city processing complete

# merge csv and shapefiles for county ratio (use later) and pop city density (use now) calculations
city = gpd.read_file('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_place10/tl_2010_place.shp')
inc = pd.read_csv('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/Incorporated.csv')
new = inc.merge(city, left_on='Name', right_on='NAME10')
new = new.drop(['Name','geometry'], axis = 1)
new['urban_pop'] = pd.to_numeric(new['urban_pop'])
new['ALAND_SQMI'] = pd.to_numeric(new['ALAND_SQMI'])
new['density'] = pd.eval('new.urban_pop / new.ALAND_SQMI')
new.to_csv('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/inc_with_pop_list.csv')
# city pop merge complete

# create county urban population pivot table to merge with shapefile
urban = pd.read_csv('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/inc_with_pop_list.csv')
urban = urban.drop(['NAME10','ALAND10','AWATER10','INTPTLAT10','INTPTLON10','GEOID','ALAND_SQMI','AWATER_SQM','density'], axis = 1)
for col in urban.columns:
    urban['urban_pop'][urban['urban_pop'] <= 2500] = 0
urban = pd.pivot_table(urban,index=['County'],values=['urban_pop'],aggfunc=np.sum)
urban.to_csv('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/urban_by_county_pop.csv')
# county urban pops pivot table complete

# county geojson start
# merge csv with shapefile
cpop = pd.read_csv('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/counties_list_19.txt', delimiter="\t")
cshape = gpd.read_file('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_county10/tl_2010_19_county10.shp')
urban = pd.read_csv('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/urban_by_county_pop.csv')
cshape["GEOID10"] = pd.to_numeric(cshape["GEOID10"])
cshape["INTPTLAT10"] = pd.to_numeric(cshape["INTPTLAT10"])
cshape["INTPTLON10"] = pd.to_numeric(cshape["INTPTLON10"])
cshape = cshape.merge(cpop, left_on='GEOID10', right_on='GEOID')
cshape = cshape.merge(urban, left_on='NAME10',right_on='County')
cshape.rename(columns={'POP10_y':'urban_pop'}, inplace=True)
cshape['rural_pop'] = cshape.POP10 - cshape.urban_pop
cshape['rural_perc'] = cshape.rural_pop / cshape.POP10 * 100
cshape['urban_perc'] = cshape.urban_pop / cshape.POP10 * 100
cshape.to_file(os.path.join('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_county10/tl_2010_19_county.shp'))
        
# reduce attributes
cf = gpd.read_file('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_county10/tl_2010_19_county.shp')
cf.explode()
cf = cf.drop(['COUNTYFP10', 'COUNTYNS10', 'GEOID10', 'NAMELSAD10', 'LSAD10', 'CLASSFP10', 'MTFCC10', 'CSAFP10', 'CBSAFP10', 'METDIVFP10', 'FUNCSTAT10', 'USPS', 'ANSICODE', 'NAME', 'HU10', 'ALAND', 'AWATER', 'INTPTLAT', 'INTPTLONG', 'County'], axis = 1)
cf.to_file(os.path.join('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_county10/tl_2010_county.shp'))

# read the shapefile
reader = shapefile.Reader('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_county10/tl_2010_county.shp','r')
fields = reader.fields[1:]
field_names = [field[0] for field in fields]
buffer = []
for sr in reader.shapeRecords():
       atr = dict(zip(field_names, sr.record))
       geom = sr.shape.__geo_interface__
       buffer.append(dict(type="Feature", \
        geometry=geom, properties=atr))
   
# produce the GeoJSON file
geojson = open('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/county.geojson', 'w')
geojson.write(dumps({"type": "FeatureCollection",\
"features": buffer}, indent=2) + "\n")
geojson.close()
# county processing complete

# create state urban and rural population pivot table
spop = gpd.read_file('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/tl_2010_19_county10/tl_2010_county.shp')
spop = spop.drop(['NAME10','ALAND10','AWATER10','INTPTLAT10','INTPTLON10','GEOID','ALAND_SQMI','AWATER_SQM','rural_perc','urban_perc'], axis = 1)
spop = pd.pivot_table(spop,index=['STATEFP10'],values=['POP10','urban_pop','rural_pop'],aggfunc=np.sum)
spop.to_csv('D:/Documents/Education/VU/Courses/Internet_GIS/Assignment_Adv/Data/2010_data/state_pops.csv')
# state urban/rural population pivot table complete