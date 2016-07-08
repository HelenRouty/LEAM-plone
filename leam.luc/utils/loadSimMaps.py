import os, sys
import optparse
from os.path import walk
from leamsite import LEAMsite

pathmap = {
    'subregional-maps': 'projections/subregional',
    'no-growth-maps': 'drivers/nogrowth',
    'transportation-network': 'drivers/transportation',
    'cities-attractor': 'drivers/attractors',
    'employment-attractor': 'drivers/attractors',
    'regional-attractors': 'drivers/attractors',
    'initial-landuse': 'drivers/grids',
    'special-drivers': 'drivers/specials',
    }


def getFSS(fss):
    f = open(fss+'/fss.cfg')
    for l in f.readlines():
        if l.startswith('simimage'):
            simmap = l.split('=')[1].strip()
        elif l.startswith('mapfile'):
            mapfile = l.split('=')[1].strip()
    return ('/'.join((fss,simmap)), '/'.join((fss, mapfile)))

def processFSS(params, dirname, fnames):
    fsspath, srcurl, dsturl = params
    if 'fss.cfg' in fnames:
        simmap, mapfile = getFSS(dirname)
        relpath = dirname[len(fsspath):]
        relpath = relpath.split('/')
        if len(relpath) == 2:
            url = '/'.join((srcurl, relpath[0], relpath[1]))
            data = srcsite.getSimMap(url)
            u = '/'.join((dsturl, pathmap[relpath[0]]))
            print data['title'], ">>>>", u
            dstsite.putSimMap(simmap, mapfile, u, title=data['title'],
                trans=data['transparency'], details=data['details'],
                zoom = data['zoom'])
             

def main():
    global srcsite, dstsite

    usage = "usage: %prog [options] <fss> <src URL> <dst URL>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option
    parser.add_option("-u", "--user", default="admin",
        help="Plone user")
    parser.add_option("-p", "--password", default="leam4z",
        help="Plone user's password")

    (opts, args) = parser.parse_args()

    if len(args) != 3:
        parser.error("the URL and the fss path are required")
    else:
        fss, src, dst = args


    srcsite = LEAMsite(src, user=opts.user, passwd=opts.password)
    if srcsite.error:
        parser.error("the URL '%s' is not a valid site" % src)

    dstsite = LEAMsite(dst, user=opts.user, passwd=opts.password)
    if dstsite.error:
        parser.error("the URL '%s' is not a valid site" % dst)

    walk(fss, processFSS, (fss, src, dst))


if __name__ == "__main__":
    main()
