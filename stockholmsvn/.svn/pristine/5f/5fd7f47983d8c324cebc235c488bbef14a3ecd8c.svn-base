#!/usr/bin/env python

import os, sys
import subprocess

gisrc_tmpl = """
GISDBASE: %(GISDBASE)s
LOCATION_NAME: %(LOCATION_NAME)s
MAPSET: %(MAPSET)s
GRASS_GUI: text
"""


GRASSBIN = '/usr/bin/grass'

def importShapefile(gname, fname):
    os.system('v.in.ogr  --overwrite dsn=%s output=%s location=tmp$$' %
              (fname, gname))
    os.system('v.proj --overwrite input=%s mapset=PERMANENT location=tmp$$ output=%s' % (gname, gname))
    os.system('rm -rf ./tmp$$')


class GRASS:
    "wrapper for GRASS functions"

    def __init__(self, location, mapset, gisrc='./gisrc', gisdbase='.'):
        self.oldpath = os.environ['PATH']
        self.env = {
           'GRASS_GUI': 'text', 
           'GRASS_PAGER':'cat', 
           'GRASS_PYTHON':'python', 
           'LD_LIBRARY_PATH':'/usr/lib/grass64/lib', 
           'GISBASE': '/usr/lib/grass64',
        }
        self.env['PATH'] = ':'.join(['/usr/lib/grass64/bin',
                                     '/usr/lib/grass64/scripts', 
                                     os.environ['PATH']
                                   ])
        self.env['GISDBASE'] = gisdbase
        self.env['LOCATION_NAME'] = location
        self.env['MAPSET'] = mapset
        self.env['GISRC'] = gisrc

        f = open(self.env['GISRC'], 'w')
        f.write(gisrc_tmpl % self.env)
        f.close

    def setEnv(self):
        os.environ.update(self.env)

    def getPath(self):
        return os.path.join(self.env['GISDBASE'],
                  self.env['LOCATION_NAME'],self.env['MAPSET'])

    def locationPath(self):
        return os.path.join(self.env['GISDBASE'],
                  self.env['LOCATION_NAME'])

    def getEnv(self):
        return self.env

    def runGrass(self):
            p = subprocess.Popen([GRASSBIN, self.getPath()], shell=False,
                                 stdout=subprocess.PIPE)
            out = p.communicate()[0]
   

    # subprocess call doesn't seem to be working
    def cmd(self, exe, *args):
        exe = os.path.join(self.env['GISBASE'],'bin',exe)
        retval = subprocess.call((exe,)+args, shell=False, env=self.env,
                         stdin=None, stdout=subprocess.PIPE, 
                         stderr=subprocess.STDOUT)
        return retval


def main():
    location = sys.argv[1]
    mapset = sys.argv[2]

    g = GRASS(location, mapset)
    g.setEnv()

    print g.getEnv()
    print g.getPath()

    os.system('g.list type=rast')
    #g.cmd('g.list', 'type=rast')


if __name__ == "__main__":
    main()
