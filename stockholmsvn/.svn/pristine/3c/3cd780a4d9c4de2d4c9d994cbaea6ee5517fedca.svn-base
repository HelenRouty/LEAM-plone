GLUC = /usr/local/bin/gluc
DATA = ./gluc/Data
MAPS = ./gluc/DriverOutput/Maps

start:
	r.mapcalc change=0
	r.out.gdal input=change output=gluc/DriverOutput/Maps/change.bil format=EHdr type=Byte
	r.mapcalc summary=0
	r.out.gdal input=summary output=gluc/DriverOutput/Maps/summary.bil format=EHdr type=Byte
	r.mapcalc ppcell=0.0
	r.mapcalc hhcell=0.0
	r.mapcalc empcell=0.0
	r.mapcalc year=0

growth:
	${GLUC} -r -d -ppath . -p gluc -ci ${PROJID}.conf
	r.in.gdal --overwrite input=${MAPS}/change.bil output=${PROJID}_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=${PROJID}_summary
	r.mapcalc "${PROJID}_ppcell=if(${PROJID}_change==21,pop_density,0)"
	r.mapcalc "${PROJID}_hhcell=${PROJID}_ppcell/2.6"
	r.mapcalc "${PROJID}_empcell=if(${PROJID}_change==23,emp_density,0)"
	r.mapcalc "${PROJID}_year=if(${PROJID}_summary>0,${PROJID}_summary+${START},0)"

decline:
	${GLUC} -r -d -ppath . -p gluc -ci ${PROJID}.conf
	r.in.gdal --overwrite input=${MAPS}/change.bil output=${PROJID}_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=${PROJID}_summary
	r.mapcalc "${PROJID}_ppcell=if(${PROJID}_change==21,-1*pop_density,0)"
	r.mapcalc "${PROJID}_hhcell=${PROJID}_ppcell/2.6"
	r.mapcalc "${PROJID}_empcell=if(${PROJID}_change==23,-1*emp_density,0)"
	r.mapcalc "${PROJID}_year=if(${PROJID}_summary>0,${PROJID}_summary+${START},0)"

region:
	${GLUC} -r -d -ppath . -p gluc -ci ${PROJID}.conf
	r.in.gdal --overwrite input=${MAPS}/change.bil output=${PROJID}_change
	r.mapcalc "change=if(${PROJID}_change,${PROJID}_change,change)"
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=${PROJID}_summary
	r.mapcalc "${PROJID}_ppcell=if(${PROJID}_change==21,pop_density,0.0)"
	r.mapcalc "${PROJID}_hhcell=${PROJID}_ppcell/2.6"
	r.mapcalc "${PROJID}_empcell=if(${PROJID}_change==23,emp_density,0.0)"
	r.mapcalc "${PROJID}_year=if(${PROJID}_summary>0,${PROJID}_summary+${START},0)"

merge:
	r.mapcalc "change=if(${PROJID}_change,${PROJID}_change,change)"
	r.mapcalc "summary=if(${PROJID}_summary,${PROJID}_summary,summary)"
	r.mapcalc "ppcell=if(${PROJID}_ppcell,${PROJID}_ppcell,ppcell)"
	r.mapcalc "hhcell=if(${PROJID}_hhcell,${PROJID}_hhcell,hhcell)"
	r.mapcalc "empcell=if(${PROJID}_empcell,${PROJID}_empcell,empcell)"
	r.mapcalc "year=if(${PROJID}_year,${PROJID}_year,year)"

write:
	r.out.gdal input=change output=change.gtif type=Byte
	r.out.gdal input=summary output=summary.gtif type=Byte
	r.out.gdal -c input=ppcell output=ppcell.gtif type=Float32
	r.out.gdal -c input=hhcell output=hhcell.gtif type=Float32
	r.out.gdal -c input=empcell output=empcell.gtif type=Float32
	r.out.gdal -c input=year output=year.gtif type=Int32
	zip model_results.zip ppcell.gtif hhcell.gtif empcell.gtif change.gtif year.gtif

run:
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf

all: spatial franklin jefferson madison monroe stcharles stclair stlouiscity stlouis
	r.mapcalc "change=franklin_change+jefferson_change+madison_change+monroe_change+stclair_change+stlouiscity_change+stlouis_change"
	r.mapcalc "summary=franklin_summary+jefferson_summary+madison_summary+monroe_summary+stclair_summary+stlouiscity_summary+stlouis_summary"
	r.mapcalc "ppcell=franklin_ppcell+jefferson_ppcell+madison_ppcell+monroe_ppcell+stclair_ppcell+stlouiscity_ppcell+stlouis_ppcell"
	r.mapcalc "hhcell=franklin_hhcell+jefferson_hhcell+madison_hhcell+monroe_hhcell+stclair_hhcell+stlouiscity_hhcell+stlouis_hhcell"
	r.mapcalc "empcell=franklin_empcell+jefferson_empcell+madison_empcell+monroe_empcell+stclair_empcell+stlouiscity_empcell+stlouis_empcell"

franklin:
	r.out.gdal input=$@ output=${DATA}/boundary.bil format=EHdr type=Byte 
	cp ${DATA}/$@_demand.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,emp_density,0)"

jefferson:
	r.out.gdal input=$@ output=${DATA}/boundary.bil format=EHdr type=Byte 
	cp ${DATA}/$@_demand.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,emp_density,0)"


madison:
	r.out.gdal input=$@ output=${DATA}/boundary.bil format=EHdr type=Byte 
	cp ${DATA}/$@_demand.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,emp_density,0)"

monroe:
	r.out.gdal input=$@ output=${DATA}/boundary.bil format=EHdr type=Byte 
	cp ${DATA}/$@_demand.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,emp_density,0)"

stcharles:
	r.out.gdal input=$@ output=${DATA}/boundary.bil format=EHdr type=Byte 
	cp ${DATA}/$@_demand.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,emp_density,0)"

stcharles_altgrowth:
	cp ${DATA}/stcharles_alt.graphs ${DATA}/demand.graphs
	r.out.gdal input=pop_density output=${DATA}/pop_density.bil format=EHdr type=Float32
	r.out.gdal input=stcharles_growth output=${DATA}/boundary.bil format=EHdr type=Byte 
	r.out.gdal input=redev output=${DATA}/landcover.bil format=EHdr type=Byte
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,emp_density,0)"

stcharles_altdecline:
	cp ${DATA}/stcharles_alt.graphs ${DATA}/demand.graphs
	r.out.gdal input=pop_density output=${DATA}/pop_density.bil format=EHdr type=Float32
	r.out.gdal input=redev output=${DATA}/landcover.bil format=EHdr type=Byte
	r.out.gdal input=stcharles_decline output=${DATA}/boundary.bil format=EHdr type=Byte 
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,-1*pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,emp_density,0)"


stclair:
	r.out.gdal input=$@ output=${DATA}/boundary.bil format=EHdr type=Byte 
	cp ${DATA}/$@_demand.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,emp_density,0)"

stlouiscity: stlouiscity_demand stlouiscity_decline
	r.mapcalc "$@_change=stlouiscity_demand_change+stlouiscity_decline_change"
	r.mapcalc "$@_summary=stlouiscity_demand_summary+stlouiscity_decline_summary"
	r.mapcalc "$@_ppcell=stlouiscity_demand_ppcell+stlouiscity_decline_ppcell"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=stlouiscity_demand_empcell+stlouiscity_decline_empcell"

stlouiscity_post:
	r.out.gdal input=stlouiscity_demand_change output=stlouiscity_demand_change.gtif
	./bin/leamsite.py -n admin -p leam4z -u ${URL} --putsimmap stlouiscity_demand_change.gtif change.map
	r.out.gdal input=stlouiscity_decline_change output=stlouiscity_decline_change.gtif
	./bin/leamsite.py -n admin -p leam4z -u ${URL} --putsimmap stlouiscity_decline_change.gtif change.map


stlouiscity_demand: allgrowth.bil redev_probmap.bil
	r.out.gdal input=stlouiscity output=${DATA}/boundary.bil format=EHdr type=Byte 
	r.out.gdal input=developed_res output=${DATA}/landcover.bil format=EHdr type=Byte 
	r.mapcalc "p=pop_density*2.5"
	r.out.gdal input=p output=${DATA}/pop_density.bil format=EHdr type=Float32
	r.mapcalc "p=emp_density*2.5"
	r.out.gdal input=p output=${DATA}/emp_density.bil format=EHdr type=Float32
	cp ${DATA}/$@.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,emp_density,0)"
	
stlouiscity_decline: allgrowth.bil redev_probmap.bil
	r.out.gdal input=stlouiscity output=${DATA}/boundary.bil format=EHdr type=Byte 
	r.out.gdal input=developed_com output=${DATA}/landcover.bil format=EHdr type=Byte 
	r.mapcalc "p=pop_density*2.5"
	r.out.gdal input=p output=${DATA}/pop_density.bil format=EHdr type=Float32
	r.out.gdal input=existing_emp output=${DATA}/emp_density.bil format=EHdr type=Float32
	cp ${DATA}/$@.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,-2.5*pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,-1*existing_emp,0)"

stlouis: stlouis_demand stlouis_decline_res stlouis_decline_com
	r.mapcalc "$@_change=stlouis_demand_change+stlouis_decline_res_change+stlouis_decline_com_change"
	r.mapcalc "$@_summary=stlouis_demand_summary+stlouis_decline_res_summary+stlouis_decline_com_summary"
	r.mapcalc "$@_ppcell=stlouis_demand_ppcell+stlouis_decline_res_ppcell+stlouis_decline_com_ppcell"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=stlouis_demand_empcell+stlouis_decline_res_empcell+stlouis_decline_com_empcell"

stlouis_demand: landcover.bil nogrowth.bil
	r.out.gdal input=stlouis output=${DATA}/boundary.bil format=EHdr type=Byte 
	cp ${DATA}/$@.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,emp_density,0)"

stlouis_decline_res: allgrowth.bil
	r.out.gdal input=stlouis output=${DATA}/boundary.bil format=EHdr type=Byte 
	r.out.gdal input=developed_res output=${DATA}/landcover.bil format=EHdr type=Byte 
	cp ${DATA}/$@.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,-1*pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,-1*emp_density,0)"

stlouis_decline_com: developed_com allgrowth.bil
	r.out.gdal input=stlouis output=${DATA}/boundary.bil format=EHdr type=Byte 
	r.out.gdal input=developed_com output=${DATA}/landcover.bil format=EHdr type=Byte 
	cp ${DATA}/$@.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,-1*pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,-1*emp_density,0)"

stlouis_enhanced: stlouis_demand_enhanced stlouis_decline_enhanced_res stlouis_decline_enhanced_com

stlouis_enhanced_post:
	r.out.gdal input=stlouis_demand_enhanced_change output=stlouis_demand_enhanced_change.gtif
	./bin/leamsite.py -n admin -p leam4z -u ${URL} --putsimmap stlouis_demand_enhanced_change.gtif change.map
	r.out.gdal input=stlouis_decline_enhanced_res_change output=stlouis_decline_enhanced_res_change.gtif
	./bin/leamsite.py -n admin -p leam4z -u ${URL} --putsimmap stlouis_decline_enhanced_res_change.gtif change.map
	r.out.gdal input=stlouis_decline_enhanced_com_change output=stlouis_decline_enhanced_com_change.gtif
	./bin/leamsite.py -n admin -p leam4z -u ${URL} --putsimmap stlouis_decline_enhanced_com_change.gtif change.map

stlouis_demand_enhanced: landcover.bil nogrowth.bil
	r.out.gdal input=stlouis output=${DATA}/boundary.bil format=EHdr type=Byte 
	r.mapcalc "p=pop_density*2.5"
	r.out.gdal input=p output=${DATA}/pop_density.bil format=EHdr type=Float32
	r.mapcalc "p=emp_density*2.5"
	r.out.gdal input=p output=${DATA}/emp_density.bil format=EHdr type=Float32
	cp ${DATA}/$@.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.colors $@_change rules=change.txt
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,emp_density,0)"

stlouis_decline_enhanced_res: allgrowth.bil redev_probmap.bil
	r.out.gdal input=stlouis output=${DATA}/boundary.bil format=EHdr type=Byte 
	r.out.gdal input=developed_res output=${DATA}/landcover.bil format=EHdr type=Byte 
	r.mapcalc "p=pop_density*2.5"
	r.out.gdal input=p output=${DATA}/pop_density.bil format=EHdr type=Float32
	r.mapcalc "p=emp_density*2.5"
	r.out.gdal input=p output=${DATA}/emp_density.bil format=EHdr type=Float32
	cp ${DATA}/$@.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.colors $@_change rules=change.txt
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,-2.5*pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,-2.5*emp_density,0)"

stlouis_decline_enhanced_com: allgrowth.bil redev_probmap.bil
	r.out.gdal input=stlouis output=${DATA}/boundary.bil format=EHdr type=Byte 
	r.out.gdal input=developed_com output=${DATA}/landcover.bil format=EHdr type=Byte 
	r.mapcalc "p=pop_density*2.5"
	r.out.gdal input=p output=${DATA}/pop_density.bil format=EHdr type=Float32
	r.out.gdal input=existing_emp output=${DATA}/emp_density.bil format=EHdr type=Float32
	cp ${DATA}/$@.graphs ${DATA}/demand.graphs
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf > $@.log 2>&1
	r.in.gdal --overwrite input=${MAPS}/change.bil output=$@_change
	r.colors $@_change rules=change.txt
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=$@_summary
	r.mapcalc "$@_ppcell=if($@_change==21,-2.5*pop_density,0)"
	r.mapcalc "$@_hhcell=$@_ppcell/2.6"
	r.mapcalc "$@_empcell=if($@_change==23,-1*existing_emp,0)"

spatial: landcover.bil nogrowth.bil floodplain.bil res_probmap.bil com_probmap.bil pop_density.bil emp_density.bil
	touch spatial_maps


gluc: boundary.bil landcover.bil nogrowth.bil floodplain.bil res_probmap.bil com_probmap.bil
	${GLUC} -r -d -ppath . -p gluc -ci baseline.conf
	r.in.gdal --overwrite input=${MAPS}/change.bil output=change
	r.in.gdal --overwrite input=${MAPS}/summary.bil output=summary
	r.mapcalc dev='if(change)'
	r.mapcalc res='if(change==21)'
	r.mapcalc com='if(change==23)'
	-g.remove rast=ppcell,hhcell,empcell
	r.recode input=summary output=ppcell rules=./SFA/ppcell.recode
	r.mapcalc ppcell=res*ppcell
	r.recode input=summary output=hhcell rules=./SFA/hhcell.recode
	r.mapcalc hhcell=res*hhcell
	r.recode input=summary output=empcell rules=./SFA/empcell.recode
	r.mapcalc empcell=com*empcell

boundary.bil:
	r.null boundary null=0
	r.out.gdal input=boundary output=${DATA}/boundary.bil format=EHdr type=Byte 

landcover.bil:
	r.out.gdal input=landcover output=${DATA}/landcover.bil format=EHdr type=Byte

developed_res:
	r.mapcalc "$@=if(landcover==21||landcover==22, 82, 24)"

developed_com:
	r.mapcalc "$@=if(landcover==23||landcover==24, 82, 24)"

nogrowth.bil:
	r.out.gdal input=noGrowth output=${DATA}/nogrowth.bil format=EHdr type=Byte

allgrowth.bil:
	r.mapcalc "d=0"
	r.out.gdal input=d output=${DATA}/nogrowth.bil format=EHdr type=Byte 

floodplain.bil:
	r.out.gdal input=floodplain output=${DATA}/floodplain.bil format=EHdr type=Byte

pop_density.bil:
	r.out.gdal input=pop_density output=${DATA}/pop_density.bil format=EHdr type=Float32

emp_density.bil:
	r.out.gdal input=emp_density output=${DATA}/emp_density.bil format=EHdr type=Float32

res_probmap.bil:
	r.null res_probmap null=0.0
	r.out.gdal input=res_probmap output=${DATA}/res_probmap.bil format=EHdr type=Float32

com_probmap.bil:
	r.null com_probmap null=0.0
	r.out.gdal input=com_probmap output=${DATA}/com_probmap.bil format=EHdr type=Float32

redev_probmap.bil:
	r.null redev_probmap null=0.0
	r.out.gdal input=redev_probmap output=${DATA}/res_probmap.bil format=EHdr type=Float32
	r.out.gdal input=redev_probmap output=${DATA}/com_probmap.bil format=EHdr type=Float32
