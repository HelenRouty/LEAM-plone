
r.out.gdal input=change output=change.gtif type=Byte
python bin/leamsite.py -u $1 --putsimmap change.gtif ./results/change.map -t 'LU State Change'
r.out.gdal input=ppcell output=ppcell.gtif type=Byte
#python bin/leamsite.py -u $1 --putsimmap ppcell.gtif ./results/ppcell.map -t 'Population'
r.out.gdal input=empcell output=empcell.gtif type=Byte
#python bin/leamsite.py -u $1 --putsimmap empcell.gtif ./results/empcell.map -t 'Employment'
r.out.gdal input=year output=year.gtif type=Byte
python bin/leamsite.py -u $1 --putsimmap year.gtif ./results/year.map -t 'Year'

r.neighbors -c input=ppcell output=ppcell_heat method=sum size=11
r.neighbors -c input=empcell output=empcell_heat method=sum size=11


#rm raster_results.zip
#r.out.gdal input=ppcell output=popcell.gtif type=Float32
#r.out.gdal input=hhcell output=hhcell.gtif type=Float32
#r.out.gdal input=empcell output=empcell.gtif type=Float32
#zip raster_results.zip change.gtif summary.gtif hhcell.gtif popcell.gtif empcell.gtif
#bin/leamsite.py -u http://datacenter.leamgroup.com/ewg/scenarios/$1 --putfile raster_results.zip -t 'Results in Raster Format'

#rm probmaps.zip
#r.out.gdal input=res_probmap output=probmap_res.gtif type=Float32
#r.out.gdal input=com_probmap output=probmap_com.gtif type=Float32
#zip probmaps.zip probmap_res.gtif probmap_com.gtif
#bin/leamsite.py -u http://datacenter.leamgroup.com/ewg/scenarios/$1 --putfile probmaps.zip -t 'Static Probability Maps'

#r.out.gdal input=probmap_half output=probmap_half.gtif type=Int32
#bin/leamsite.py -u http://datacenter.leamgroup.com/ewg/scenarios/$1 --putfile probmaps.zip -t 'Static Probability Maps'

rm popemp_bysections.*
g.remove vect=popemp_bysection rast=popemp_bysection
g.copy vect=section,popemp_bysection

r.mapcalc "ppcell_2020=if(year<=2020,ppcell,0)"
v.rast.sum zones=popemp_bysection input=ppcell_2020 column=POP2020
r.mapcalc "hhcell_2020=if(year<=2020,hhcell,0)"
v.rast.sum zones=popemp_bysection input=hhcell_2020 column=HH2020
r.mapcalc "empcell_2020=if(year<=2020,empcell,0)"
v.rast.sum zones=popemp_bysection input=empcell_2020 column=EMP2020

r.mapcalc "ppcell_2030=if(year<=2030,ppcell,0)"
v.rast.sum zones=popemp_bysection input=ppcell_2030 column=POP2030
r.mapcalc "hhcell_2030=if(year<=2030,hhcell,0)"
v.rast.sum zones=popemp_bysection input=hhcell_2030 column=HH2030
r.mapcalc "empcell_2030=if(year<=2030,empcell,0)"
v.rast.sum zones=popemp_bysection input=empcell_2030 column=EMP2030

r.mapcalc "ppcell_2040=if(year<=2040,ppcell,0)"
v.rast.sum zones=popemp_bysection input=ppcell_2040 column=POP2040
r.mapcalc "hhcell_2040=if(year<=2040,hhcell,0)"
v.rast.sum zones=popemp_bysection input=hhcell_2040 column=HH2040
r.mapcalc "empcell_2040=if(year<=2040,empcell,0)"
v.rast.sum zones=popemp_bysection input=empcell_2040 column=EMP2040

v.out.ogr -c input=popemp_bysection dsn=. type=area
zip popemp_bysection.zip popemp_bysection.* 
python bin/leamsite.py -u $1 --putfile popemp_bysection.zip -t 'Population and Employment Change by Section'
python bin/leamsite.py -u $1 --putsimmap popemp_bysection.zip  results/popsection.map -t 'Population by Section'
python bin/leamsite.py -u $1 --putsimmap popemp_bysection.zip  results/empsection.map -t 'Employment by Section'

#rm development_bysection.*
#g.remove vect=development_bysection rast=development_bysection
#g.copy vect=section,development_bysection
#
#r.mapcalc "res_acres_2010=if(landcover==21||landcover==22,0.222,0.0)"
#r.mapcalc "com_acres_2010=if(landcover==23,0.222,0.0)"
#v.rast.sum zones=development_bysection input=res_acres_2010 column=RES2010
#v.rast.sum zones=development_bysection input=com_acres_2010 column=COM2010
#
#r.mapcalc "res_acres_2020=if(year<=2020&&growth_change==21,0.222,0.0)"
#r.mapcalc "com_acres_2020=if(year<=2020&&growth_change==23,0.222,0.0)"
#v.rast.sum zones=development_bysection input=res_acres_2020 column=RES2020
#v.rast.sum zones=development_bysection input=com_acres_2020 column=COM2020
#v.db.update development_bysection column=RES2020 "value=RES2010+RES2020"
#v.db.update development_bysection column=COM2020 "value=COM2010+COM2020"
#
#r.mapcalc "res_acres_2030=if(year<=2030&&growth_change==21,0.222,0.0)"
#r.mapcalc "com_acres_2030=if(year<=2030&&growth_change==23,0.222,0.0)"
#v.rast.sum zones=development_bysection input=res_acres_2030 column=RES2030
#v.rast.sum zones=development_bysection input=com_acres_2030 column=COM2030
#v.db.update development_bysection column=RES2030 "value=RES2010+RES2030"
#v.db.update development_bysection column=COM2030 "value=COM2010+COM2030"
#
#r.mapcalc "res_acres_2040=if(year<=2040&&growth_change==21,0.222,0.0)"
#r.mapcalc "com_acres_2040=if(year<=2040&&growth_change==23,0.222,0.0)"
#v.rast.sum zones=development_bysection input=res_acres_2040 column=RES2040
#v.rast.sum zones=development_bysection input=com_acres_2040 column=COM2040
#v.db.update development_bysection column=RES2040 "value=RES2010+RES2040"
#v.db.update development_bysection column=COM2040 "value=COM2010+COM2040"
#
#v.out.ogr -c input=development_bysection dsn=. type=area
#zip -m development_bysection.zip development_bysection.*
#python bin/leamsite.py -u $1 --putfile development_bysection.zip -t "Total Development by Section"
#

