#!/usr/bin/env python
"""
The following script is piped through a shell to perform
necessary grass calculations.

Requires the following arguments (all strings):
cities -- name of the cities raster layer.  Each city is identified by
          by the cat number in the associated cities vector layer.
id     -- id (cat) of the city
output -- the output layer name
"""
import sys,os
from optparse import OptionParser
import grass.script as grass


usage = "usage: %prog [options] <cities>"

description = """ Iterates through each city in the <cities> 
vector layer computing a city attractor map.  Each city attractor 
map is aggregated into the final <attmap> to create a cities gravity 
map using POP/(cityatt+1)^2.
"""

def normalize(layer, result=""):
    "normalize a composity gravity map"

    if (result==""):
        result=layer+"_norm"

    for l in os.popen('r.univar %s' % layer):
        if l.startswith('maximum:'):
            break

    s, max = l.strip().split()
    os.system('r.mapcalc %s=%s/%s' % (result,layer,max))


def make_city_tt(cities, cat, overland='overlandTravelTime30', 
                 interstates='intTravelTime30', xover='cross', maxcost='60'):
    """Extracts a specific city, buffers it, and then uses r.multicost
       to determine travel time out to maxcost (minutes), and computes
       attractor maps based on pop/tt^2.
       tt -- is the travel time map
    """
    grass.mapcalc('ctmp=if($cities==$cat,1,null())', cities=cities,
        cat=cat)
    grass.run_command('r.buffer', input='ctmp', output='ctmp', dist='180')
    grass.mapcalc('ctmp=if(ctmp)')
    grass.run_command('r.multicost', input=overland, m2=interstates, 
        xover=xover, start_rast='ctmp', output='tt', max_cost=maxcost)


def main():

    os.environ['GRASS_MESSAGE_FORMAT'] = 'silent'
    grass.run_command('g.gisenv', set='OVERWRITE=1')
    mapset = grass.gisenv()['MAPSET']

    parse = OptionParser(usage=usage, description=description)
    parse.add_option('-f', '--force', action="store_true", default=False,
        help='force the rasterization of the cities vector layer')
    parse.add_option('-c', '--cat', metavar='ID',
        help='run script on a single city cat ID number')
    parse.add_option('-t', '--maxtime', metavar='MINUTES', default='60',
        help='sets the max travel time per city')
    parse.add_option('-p', '--pop', metavar='FIELDNAME', default='POP2010',
        help='name of the population field within cities')
    parse.add_option('-P', '--preserve', default=False, action="store_true",
        help='preserves the individual city travel time maps (city##_tt)')
    parse.add_option('-r', '--rebuild', default=False, action="store_true",
        help='rebuild city travel time maps even if one exists')
    parse.add_option('-m', '--mode', default="max",
        help='operate in either max or gravity mode (default=max)')

    opts, args = parse.parse_args()
    if len(args) != 1:
        parse.error("'cities' layer name rquired")
    else:
        cities = args[0]

    if opts.mode == 'grav':
        dest = 'cities_grav'
        method = '$dest=$dest+if(isnull($tt), 0.0, $pop/($tt+0.1)^2)'
    elif opts.mode == 'max':
        dest = 'cities_max'
        method = '$dest=max($dest,if(isnull($tt), 0.0, $pop/($tt+0.1)^2))'
    else:
        parse.error("option mode must be max or gravity")

    # if the cat ID of the city has been given just create the city map
    # NOTE: short-circuits the rest of the script!
    if opts.cat:
        tt = make_city_tt(cities, opts.cat, maxcost=opts.maxtime)
        grass.run_command('g.rename', rast='%s,city%s_tt' % (tt,opts.cat))
        grass.message('city%s_tt: city travel time created.' % opts.cat)
        sys.exit(0)


    grass.mapcalc("$dest=0.0", dest=dest)

    # get all the existing travel time maps
    ttmaps = grass.mlist_grouped('rast', pattern='city*_tt').get(mapset,[])

    # for each city calculate the accumulated cost surface and
    # convert gavity map by dividing population by cost squared and
    # create a composite map gravity may be summing all maps together
    catpop = grass.parse_command('v.db.select', flags='c', 
        map=cities, column='cat,'+opts.pop, fs='=')

    for cat,pop in catpop.items():
        print cat, pop
        citytt = 'city%s_tt' % cat
        if opts.rebuild or citytt not in ttmaps:
            make_city_tt(cities, cat, maxcost=opts.maxtime)
            if opts.preserve:
                grass.run_command('g.rename', rast='tt,%s' % citytt)
            else:
                citytt = 'tt'
        grass.mapcalc(method, dest=dest, pop=pop, tt=citytt)

    normalize(dest)
    print dest, "created."

if __name__ == '__main__':
     main()

