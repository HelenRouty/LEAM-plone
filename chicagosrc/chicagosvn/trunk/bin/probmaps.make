W_CITIES_RES=1.5
W_CITIES_COM=2.0
W_TRANS_RES=0.8
W_TRANS_COM=0.9
W_EMP_RES=1.0
W_EMP_COM=1.0
W_SPECIAL_RES=1.0
W_SPECIAL_COM=1.0

GRAPHS=./SFA
DATA=gluc/Data


probmaps: probmap_res probmap_com
	@echo '#########################'; echo $@ ; date 
	r.null probmap_res null=0.0
	r.null probmap_com null=0.0

write:
	r.null probmap_res null=0.0
	r.out.gdal input=probmap_res output=${DATA}/probmap_res.bil format=EHdr type=Float32
	r.null probmap_com null=0.0
	r.out.gdal input=probmap_com output=${DATA}/probmap_com.bil format=EHdr type=Float32
	



probmap_res: probmap_com_score cities_res_score emp_res_score transport_res_score special_res_score forest_score water_score slope_score
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	#g.region res=30
	r.mapcalc $@='probmap_com_score*cities_res_score*emp_res_score*transport_res_score*special_res_score*forest_score*water_score*slope_score'

#redev_probmap: probmap_com_score emp_res_score transport_res_score special_res_score forest_score water_score slope_score building_age_score pop_age_score
redev_probmap:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	#g.region res=30
	r.mapcalc $@='probmap_com_score*emp_res_score*transport_res_score*special_res_score*forest_score*water_score*slope_score*building_age_score*pop_age_score'

probmap_com: cities_com_score emp_com_score transport_com_score special_com_score forest_score water_score slope_score
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	#g.region res=30
	r.mapcalc $@='cities_com_score*emp_com_score*transport_com_score*special_com_score*forest_score*water_score*slope_score'

probmap_com_score: probmap_com
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	r.recode input=probmap_com output=$@ rules=${GRAPHS}/ComProb.sfa

cities_res_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@,tmp1
	#g.region res=30
	#r.recode input=cities_att output=tmp1 rules=${GRAPHS}/NewCitiesAttRes.sfa
	r.mapcalc $@='pow(cities_att,${W_CITIES_RES})'
	-g.remove tmp1

cities_com_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	#g.region res=30
	#r.recode input=cities_att output=tmp1 rules=${GRAPHS}/NewCitiesAttCom.sfa
	r.mapcalc $@='pow(cities_att,${W_CITIES_COM})'

emp_res_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@,tmp1
	#g.region res=30
	r.recode input=emp_att output=tmp1 rules=${GRAPHS}/EmpAttRes.sfa
	r.mapcalc $@='pow(tmp1,${W_EMP_RES})'
	-g.remove tmp1

emp_com_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@,tmp1
	#g.region res=30
	r.recode input=emp_att output=tmp1 rules=${GRAPHS}/EmpAttCom.sfa
	r.mapcalc $@='pow(tmp1,${W_EMP_COM})'
	-g.remove tmp1

transport_res_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@,tmp1
	r.recode input=transport_att output=tmp1 rules=${GRAPHS}/TransportAttRes.sfa
	r.mapcalc $@='pow(tmp1,${W_TRANS_RES})'
	-g.remove tmp1

transport_com_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@,tmp1
	r.recode input=transport_att output=tmp1 rules=${GRAPHS}/TransportAttCom.sfa
	r.mapcalc $@='pow(tmp1,${W_TRANS_COM})'
	-g.remove tmp1

special_res_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	r.mapcalc $@='pow(special_res,${W_SPECIAL_RES})'

special_com_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	r.mapcalc $@='pow(special_com,${W_SPECIAL_COM})'


water_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	r.recode input=water_att output=$@ rules=${GRAPHS}/WaterAttMeters.sfa

forest_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	r.recode input=forest_att output=$@ rules=${GRAPHS}/ForestAttMeters.sfa

slope_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	#g.region res=30
	r.recode input=slope_att output=$@ rules=${GRAPHS}/Slope.sfa

building_age_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	#g.region res=30
	r.recode input=building_age output=$@ rules=${GRAPHS}/BuildingAge.sfa

pop_age_score:
	@echo '#########################'; echo $@ ; date 
	-g.remove $@
	#g.region res=30
	r.recode input=pop_age output=$@ rules=${GRAPHS}/PopAge.sfa

