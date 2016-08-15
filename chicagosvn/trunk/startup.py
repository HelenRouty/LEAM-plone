#!/usr/bin/env python
"""
Outline --
1. initialize working directory and GRASS mapset
2. initialize GRASS environment
3. download and import TE roads, run importTEroads
4. download and import special layers
4b. download and import nogrowth layers
5. make attmaps and probmaps
6. create demand graphs
7. create config file
8. run the LEAM land use change model
9. handle post processing
"""
import os
import sys
sys.path += ['./bin']

import csv
from glob import iglob
import logging
from operator import itemgetter
from optparse import OptionParser
from osgeo import ogr
import random
import re
import shutil
import subprocess
import requests
from subprocess import call
from subprocess import check_call
from StringIO import StringIO
import time
import xml.etree.ElementTree as ET
from zipfile import BadZipfile
from zipfile import ZipFile

from luc_config import LUC
from leamsite import LEAMsite


class RunLog:
    """Utility class that wraps the standard python logging facility
    and promotes some messages to the log maintained on portal site.
    """
    def __init__(self, resultsdir, site, initmsg=''):
        self.logger = self._init_logger(__name__)
        self.log = StringIO()
        self.site = site

        if initmsg:
            self.log.write('<h2 class="runlog">'+initmsg+'</h2>\n')
        else:
            self.log.write('<h2 class="runlog">Run Started</h2>\n')
        self.logdoc = self.site.putDocument(self.log, resultsdir, 'Run Log')

    def _init_logger(self, name, level=logging.DEBUG, fname='run.log'):
        logger = logging.getLogger(name)
        logger.setLevel(level)

        handler = logging.FileHandler(fname, mode='w')
        handler.setLevel(level)
        formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def h(self, s):
        self.logger.info('>>> '+s)
        self.log.write('<h2 class="runlog">'+s+'</h2>\n')
        self.site.editDocument(self.log, self.logdoc)

    def p(self, s):
        self.logger.info(s)
        self.log.write('<p class="runlog">'+s+'</p>\n')
        self.site.editDocument(self.log, self.logdoc)

    def warn(self, s):
        self.logger.warn(s)
        self.log.write('<h2 class="runlog-warn">Warning</h2>\n')
        self.log.write('<p class="runlog-warn">' + s + '</p>\n')
        self.site.editDocument(self.log, self.logdoc)

    def error(self, s):
        self.logger.error(s)
        self.log.write('<h2 class="runlog-err">Error Detected</h2>\n')
        self.log.write('<p class="runlog-err">' + s + '</p>\n')
        self.site.editDocument(self.log, self.logdoc)

    def exception(self, s):
         self.logger.exception(s)

    def debug(self, s):
        self.logger.debug(s)


class ProjTable:
    """A utility class used to track target and actual projections.
    Once the model run is complete the results can be posted to the
    portal.
    """

    def __init__(self):
        self.period = {}
        self.pop = []
        self.emp = []

    def years(self, projid, mode, start, end):
        """store start and end date for each projection"""

        self.period[projid] = (int(start), int(end))


    def population(self, projid, mode, taract, data):
        """update population projection information

        Args:
          projid (str): short name of projection (no spaces, etc)
          mode (str): 'growth', 'decline' or 'regional'
          taract (str): 'target' or 'actual' projection
          data (list): projection values
        """ 
        self.pop.append([projid, mode, taract, 'population',] + \
                [str(x) for x in data])

    def employment(self, projid, mode, taract, data):
        """update employment projection information

        Args:
          projid (str): short name of projection (no spaces, etc)
          mode (str): 'growth', 'decline' or 'regional'
          taract (str): 'target' or 'actual' projection
          data (list): projection values
        """ 

        self.emp.append([projid, mode, taract, 'employment',] + \
                [str(x) for x in data])

    def write_csv(self, filename=''):
        """return CSV formatted string"""

        start = min([x[0] for x in self.period.values()])
        end = max([x[1] for x in self.period.values()])
        ystr = ','.join(['','','','year'] + 
                        [str(y) for y in range(int(start),int(end)+1)])
        
        records = [ystr,] + [','.join(r) for r in self.pop] \
               + [''] + [','.join(r) for r in  self.emp] + ['']
        table = '\n'.join(records)

        if filename:
            with open(filename, 'wb') as f:
                f.write(table)

        return table


def grass_config(location, mapset, 
                 gisbase='/usr/local/grass-6.4.5svn', gisdbase='.'):
    """Initialize grass from within current script.

    Note: the gisrc file is created in /tmp with a random filename
    but never deleted.

    @Return - nothing
    """

    os.environ['GISBASE'] = gisbase
    os.environ['GRASS_VERBOSE'] = '0'
    os.environ['GRASS_OVERWRITE'] = '1'
    sys.path.append(os.path.join(gisbase, 'etc', 'python'))

    # imports the grass.script module requires GISBASE be
    # set prior to import hence the somewhat convoluted process
    global grass
    __import__('grass.script')
    grass = sys.modules['grass.script']

    from grass.script.setup import init
    gisrc = init(gisbase, gisdbase, location, mapset)
    # should catch the termination of the script and cleanup gisrc


def repeat_last(arr):
    """Repeats the last element of an array to support zip operations."""
    for x in arr:
        yield x
    while True:
        yield x

def check_extent_equal(layer, parent):
    """Compares the extent of two layers"""

    parent = grass.parse_command('v.info', flags='g', map=parent)
    for k,v in parent.items():
        parent[k] = float(v)

    layer = grass.parse_command('v.info', flags='g', map=layer)
    for k,v in layer.items():
        layer[k] = float(v)

    n = layer['north'] == parent['north']
    s = layer['south'] == parent['south']
    w = layer['west'] == parent['west']
    e = layer['east'] == parent['east']
    return n and s and e and w


def check_extents(layer, parent):
    """Compares two the extents of two layers and returns 1 if
    the first (layer) is a subextent of the second (parent).  
    Returns -1 of the second (parent) is a subextent of the first (layer).
    Returns 0 otherwise, 
    """

    parent = grass.parse_command('v.info', flags='g', map=parent)
    for k,v in parent.items():
        parent[k] = float(v)

    layer = grass.parse_command('v.info', flags='g', map=layer)
    for k,v in layer.items():
        layer[k] = float(v)

    # layer's extent is within the parent's extent
    n = layer['north'] <= parent['north']
    s = layer['south'] >= parent['south']
    w = layer['west'] >= parent['west']
    e = layer['east'] <= parent['east']
    if n and s and e and w:
        return 1

    # layer's extent is within the parent's extent
    n = layer['north'] >= parent['north']
    s = layer['south'] <= parent['south']
    w = layer['west'] <= parent['west']
    e = layer['east'] >= parent['east']
    if n and s and e and w:
        return -1

    return 0


def interpolate(start, end):
    x0 = int(start[0])
    x1 = int(end[0])
    y0 = int(start[1])
    y1 = int(end[1])
    delta = float(y1-y0)/float(x1-x0)

    results = []
    for i in range(1,x1-x0):
        results.append((x0+i, round(y0+i*delta, 0)))
    return results


def getProjectionTimeSeries(proj, **kwargs):
    """Extract time series model results and store within the portal.

    Args:
      proj (dict): projection values
      kwargs (dict): overrides proj values

    Returns: 
      (tuple): population and employment change arrays
    """
    projid = proj.get('projid', '') or grass_safe(proj['id'])
    startyear = int(kwargs.get('startyear','') or proj.get('startyear'))
    endyear = int(kwargs.get('endyear','') or proj.get('endyear'))
    runlog.debug('getProjectionTimeSeries: %s, %s-%s' \
                 % (projid, startyear, endyear))

    pop = getPerCellChange(projid+'_ppcell', projid+'_year', 
                           start=startyear, end=endyear)
    emp = getPerCellChange(projid+'_empcell', projid+'_year', 
                           start=startyear, end=endyear)
    return (pop, emp)
    

def processDriverSets(dslist, prefix='', year='year'):
    """ Process each Driver Set and generate corresponding probmap.

    GRASS:
      landcoverBase (rast): created
      landcoverRedev (rast): created

    Args:
      dslist (list): a sequence of Driver Sets 
      prefix (str): prefixed to the probmaps filename
      year (str): key used to ensure Driver Sets are sorted
        
    Returns:
      str: the year of the earliest Driver Set
    """

    if not dslist:
        raise RuntimeError('One or more %s Projections were configured '
                'but no %s Driver Sets were defined.' % (prefix, prefix))

    dslist = sorted(dslist, key=itemgetter(year))
    for drivers in dslist:

        runlog.p('processing Driver Set %s for year %s' % \
                (drivers['title'], drivers[year]))

        # load landcover if one doesn't already exists
        # NOTE: Landcover is only loaded once per scenario. It must
        #   remain outside of buildProbmap incase we use cached probmaps.
        d = grass.find_file('landcoverBase', element='cell')
        if d['name'] == '':
            site.getURL(drivers['landuse'], filename='landcover')
            import_rastermap('landcover', layer='landcoverBase')
            grass.mapcalc('$redev=if($lu>20 && $lu<25,82, 11)', 
                redev='landcoverRedev', lu='landcoverBase', quiet=True)

        # download and merge nogrowth layers
        getNoGrowthLayers(drivers.get('nogrowth', []))
        grass.mapcalc('zero=0', quiet=True)

        # attempts to download the cached probmap first
        pmaps = get_rasters(drivers['download'])
        if pmaps:
            for p in pmaps:
                runlog.debug('cached probmap found: ' + p)
                import_rastermap(p, layer=p.replace('.gtif', ''))

        else:
            try:
                buildProbmaps(drivers)
                cacheProbmaps(drivers)
            except Exception as e:
                runlog.error('Unrecoverable error building probmap.')
                runlog.exception('buildProbmaps failed')
                sys.exit(4)

        writeProbmaps(prefix, drivers.get('year', ''))

        # return the startyear based on the first Driver Set
        return dslist[0][year]


def create_regional_densities(regional):
    """create regional densities to be used as the default

    The regional projection is optional but if found only the first element
    is used.

    GRASS:
      <projid>_popden (rast): created
      <projid>_empden (rast): created
      regional_popden (rast): created
      regional_empden (rast): created

    Args:
      regional (list): a potentially empty list of regional projections
    """
    if not regional:
        return

    proj = regional[0]
    projid = proj.setdefault('projid', grass_safe(proj['id']))
    
    proj['popdens'] = import_density(projid, proj['pop_density'], 'popdens', '')
    proj['empdens'] = import_density(projid, proj['emp_density'], 'empdens', '')
    grass.run_command('g.copy', rast=[proj['popdens'],'regional_popdens'])
    grass.run_command('g.copy', rast=[proj['empdens'],'regional_empdens'])


def filter_regional_projection(projections, extent='county@PERMANENT'):
    """scans projection list and removes regional projection

    GRASS:
      Imports the shapefile and creates the raster mask. The layer
      name is stored in the projection as 'boundary'.

    Args:
      projections (list): list of projections
      extent (str): layer to be used for regional extents

    Returns:
      (list,list): subregional and regional projections
    """
    subregional = []
    regional = []
    for proj in projections:
        boundary = proj.setdefault('boundary', getLayerMask(proj['layer']))
        if check_extent_equal(boundary, extent):
            runlog.p('regional projection detected, execution deferred')
            regional.append(proj)
        else:
            subregional.append(proj)

    return (subregional, regional)


def processProjections(mode, projections, startyear, 
                       sanity=True, zones='subzones'):
    """Check each projection and either run, report sanity error, or defer.

    Each projection is processed and model is either run or a sanity error
    is generated.

    No Growth Zones are handled oddly. The GLUC model only allows a single
    no growth layer during runtime.  Currently no growth layers are 
    accumulated across all Driver Sets and impact all years rather than
    only coming into effect at the desired year.  

    Side Effects:
      A GRASS layer is created based on an accumulation of the effective
      zones of each projection.  The subzones layer will be used as a
      nogrowth layer during the regional model projection.

      During processing each projection is checked for reasonableness. If
      this desired change is not possible given the modeling constraints
      a sanity.htm file is written. Insane projections are skipped and
      the model can continue if desired (but it's probably not advisable).

    Args:
      mode (str): the type of projections being processed (growth or decline)
      projections (list): a list of model projections of the config file
      startyear (str): determined by the earliest Driver Set
      sanity (bool): toggle the sanity check (default=True)
      zones (str, GRASS layer): a GRASS layer where effective zones are
        accumulated. (default='subzones')

    Returns:
      dict: 3 items
        'startyear' - startyear provided as input parameter (int)
        'deltapop' - accumulated population change (list)
        'deltaemp' - accumulated employment change (list)
    """

    # values accumulated across projections
    deltapop = [0 for i in xrange(100)]
    deltaemp = [0 for i in xrange(100)]

    # initialize zones layers if one does not exist 
    if grass.find_file(zones)['name'] == '':
        grass.mapcalc('$z=0', z=zones)

    for proj in projections:
        runlog.h('Starting Projection '+ proj['title'])
        projid = proj.setdefault('projid', grass_safe(proj['id']))
        runlog.debug('projid = ' + projid)

        proj['startyear'] = startyear
        boundary = proj.setdefault('boundary', getLayerMask(proj['layer']))

        # aggregate growthzone boundaries together to be used as nogrowth layer
        grass.mapcalc('$zones=$zones+$b', b=boundary, zones=zones)
        
        # load density maps associated with each zone
        pop_density = proj.setdefault('popdens', import_density(projid,
                proj['pop_density'], 'popdens', 'regional_popdens'))
        emp_density = proj.setdefault('empdens', import_density(projid,
                proj['emp_density'], 'empdens', 'regional_empdens'))

        # swapping between landcovers and nogrowth layers depending
        # on redev flag.
        if mode == 'decline' or proj['redevelopment'] == 'True':
            landcover = 'landcoverRedev'
            nogrowth = 'zero'
        else:
            landcover = 'landcoverBase'
            nogrowth = 'nogrowth'

        # reads demand graphs, writes demand.graph file and writes the 
        # TODO: projid graph file should be written to config file
        endyear = proj['endyear']
        ptable.years(projid, mode, startyear, endyear)
        demand = site.getURL(proj['graph']).getvalue()
        with open('gluc/Data/%s.graphs' % projid, 'w') as f:
            f.write(demand)
        with open('gluc/Data/demand.graphs', 'w') as f:
            f.write(demand)
        pop = getDemandGraph(demand, ['population'], start=startyear)
        emp = getDemandGraph(demand, ['employment'], start=startyear)
        if mode == 'decline':
            ptable.population(projid, mode, 'target', [-1 * p for p in pop])
            ptable.employment(projid, mode, 'target', [-1 * e for e in emp])
        else:
            ptable.population(projid, mode, 'target', pop)
            ptable.employment(projid, mode, 'target', emp)

        # sanity checks try to determine if the desired change is less
        # than the maximum potential change given the boundary, landuse,
        # nogrowth, and densities
        # TODO: clean this mess up
        if sanity and mode == 'growth':
            runlog.debug('starting sanity check')
            pop_insane = sanity_check(boundary, landcover, nogrowth,
                pop_density, pop[-1], ratio=1.0)
            emp_insane = sanity_check(boundary, landcover, nogrowth,
                emp_density, emp[-1], ratio=1.0)
            if pop_insane.get('msg','') or emp_insane.get('msg',''):
                runlog.error('Projection %s failed sanity check' \
                        % proj['title'])
                with open('sanity.htm', 'a') as f:
                    f.write('<h3>Sanity checked failed for %s</h3>\n' \
                            % proj['title'])
                    sanity_report(f, 'Population', pop_insane)
                    sanity_report(f, 'Employment', emp_insane)
                continue

        else:
            runlog.debug('skipping sanity check, mode = ' + mode)

        # write BIL files for the gluc model
        #
        # The projection density maps are also copied to pop_density and
        # emp_density to ensure they are set correctly for post-run
        # calculation of ppcell and empcell.
        #
        # TODO: Rewrites the landcover and nogrowth maps every time to reflect
        # the redev flag.  With the use of dynamic gluc configuration files
        # this section can be improved.
        print "Writing BIL layers for model.............."
        runlog.debug('writing BIL layers for model')
        grass.run_command('r.out.gdal', _input=boundary, 
            output='gluc/Data/boundary.bil', _format='EHdr', _type='Byte')
        grass.run_command('r.out.gdal', _input=landcover,
                output='gluc/Data/landcover.bil', _format='EHdr', _type='Byte')
        grass.run_command('r.out.gdal', _input=nogrowth,
                output='gluc/Data/nogrowth.bil', _format='EHdr', _type='Byte')
        grass.run_command('g.copy', rast=[pop_density,'pop_density'])
        grass.run_command('g.copy', rast=[emp_density,'emp_density'])
        grass.run_command('r.out.gdal', _input=pop_density,
                output='gluc/Data/pop_density.bil',
                _format='EHdr', _type='Float32')
        grass.run_command('r.out.gdal', _input=emp_density,
                output='gluc/Data/emp_density.bil',
                _format='EHdr', _type='Float32')

        # run the GLUC model
        print "Running the GLUC model............."
        writeConfig(confname=projid, prefix=mode+'_', 
                    start=startyear, end=endyear)
        executeModel(projid, mode, startyear)

        # Extract the time series change in pop and emp from the model run
        # and accumulate it for use when setting up the regional model run.
        # For decline projections the number returned should be negative.
        pop,emp = getProjectionTimeSeries(proj, projlen=len(deltapop))
        ptable.population(projid, mode, 'actual', pop)
        ptable.employment(projid, mode, 'actual', emp)

        deltapop = [sum(x) for x in zip(deltapop, repeat_last(pop))]
        deltaemp = [sum(x) for x in zip(deltaemp, repeat_last(emp))]

    return dict(startyear=startyear, deltapop=deltapop, deltaemp=deltaemp)


def writeConfig(confname='baseline.conf',
                start='2010', end='2040',
                prefix='', probmaps=False,
                tmpl='gluc/Config/baseline.tmpl',
                path='gluc/Config'):
    """ write a GLUC config file from a template.

    PREFIX,START_DATE, and END_DATE are replaced in the template. PREFIX
    is applied to probability maps name but the START_DATE is not.  The
    GLUC model automatically appends the year during model execution.

    @confname - name of config file to be written (.conf appended if needed)
    @prefix - prefix applied to probmap names (growth, decline)
    @start - fills the START_DATE parameter in the template
    @end - fills the END_DATE parameter in the template
    @probmaps - toggle initial and final probmaps writing 
    @tmpl - name of the temlate config file
    @path - destination for 
    @Return - nothing
    """
    runlog.debug('writeConfig: confname=%s, prefix=%s, start=%s, end=%s' % \
                  (confname, prefix, start, end))

    # cleanup confname and add path
    if not confname.endswith('.conf'):
        confname += '.conf'
    config = os.path.join(path, os.path.basename(confname))

    # read the template file into string
    with open(tmpl, 'r') as f:
        template = f.read()

    d = dict(PREFIX=prefix, START_DATE=start, END_DATE=end)
    with open(config, 'w') as f:
        f.write(template.format(**d))
        if probmaps:
            f.write('* INITIAL_PROB_RES_MAP    M(M, 4, initial_probmap_res)\n')
            f.write('* INITIAL_PROB_COM_MAP    M(M, 4, initial_probmap_com)\n')
            f.write('* FINAL_PROB_RES_MAP    M(M, 4, final_probmap_res)\n')
            f.write('* FINAL_PROB_COM_MAP    M(M, 4, final_probmap_com)\n')


def executeModel(projid, mode, start):
    """ Run the GLUC model using gluc.make.

    Args:
      projid (str, simple): projection identifier used in log
      mode (str): gluc.make mode (growth, decline, region)
      start (str): start year passed as variable to gluc.make

    Returns:
      None
    """

    runlog.debug('executeModel: projid = ' + projid)

    start = str(start)

    try:
        with open('%s_gluc_make.out' % projid, 'w') as out, \
                open('%s_gluc_make.log' % projid, 'w') as err:
            cmd = 'make -f ./bin/gluc.make %s merge PROJID=%s START=%s' \
                % (mode, projid, start)
            check_call(cmd.split(), stdout=out, stderr=err)

    except subprocess.CalledProcessError: 
        runlog.error('GLUC Model Failure')
        runlog.exception('check %s_gluc_make.log' % projid)
        sys.exit(5)


def parseDemand(data, graphs):

    f = csv.reader(StringIO(data))
    for rec in f:

        if len(rec) == 0 or rec[0].startswith('#'):
            continue

        elif rec[0].strip().lower() in graphs:
            gname = rec[0].strip().lower()

            timeseries = []
            for rec in f:
                if len(rec) == 0:
                    break

                # what if int convertsion fails?
                elif len(rec) == 2:
                    timeseries.append((int(rec[0]), int(rec[1])))

                # incorrect number of fields in records
                # ignore or throw error?
                else:
                    pass

            # return graph's name and time series data
            return gname, timeseries

    # unable to parse demand file
    return None, None


def getDemandGraph(demand, gname, start=2010, delta=True):
    """Scrapes the demand graph string and extracts a time series.

    Always provides a time series starting with starting year <start> and
    ending with the final demand graph year. If the demand graph starts prior
    to the start year, the time series is truncated.  If the demand graph
    starts later than the start year then the time series is filled using
    the value of the first available year.

    Args:
      demand (str): demand graph
      gname (list of str): name of graphs desired
      start (int): desired starting year
      delta (bool):  toogles delta mode by subtracting the first element
        from each subsequent element (default=True)

    Returns:
       list of floats: an interpolated demand list
    """

    start = int(start)

    gname, vals = parseDemand(demand, gname)
    vals = sorted(vals, key=itemgetter(0))
    for i in range(len(vals)-1):
        vals.extend(interpolate(vals[i], vals[i+1]))
    vals = sorted(vals, key=itemgetter(0))

    # pad the beginning of the projection if necessary
    if vals[0][0] > start:
        vals = [(y,vals[0][1]) for y in range(start,vals[0][0])] + vals

    # drop the beginning of the projection if necessary
    elif vals[0][0] < start:
        vals = vals[start-vals[0][0]:]

    # return absolutes or deltas based on delta flag
    ts = [x[1] for x in vals]
    if delta:
        ts = [x-ts[0] for x in ts]

    return ts


def writeDemand(title, pop, emp, fname='gluc/Data/demand.graphs'):
    """Writes a minimal demand.graphs file with population and employment."""

    with open(fname, 'w') as f:
        f.write('# %s\n\n' % title)
        f.write('Population\n')
        for y,v in pop:
            f.write('%s, %s\n' % (str(y), str(v)))

        f.write('\n\nEmployment\n')
        for y,v in emp:
            f.write('%s, %s\n' % (str(y), str(v)))


def grass_safe(s):
    """Generate a string that is safe to use as a GRASS layer.

    Designed to handle filename with path and extensions but should
    work on any string. Currently performs the following steps:
    1) removes filename extension from basename and strip whitespace
    2a) removes any none alphabetic characters from the beginning
    2b) removes anything that does match a-z, A-Z, 0-9, _, -, or whitespace
    3) replaces remaining whitespaces and dashes with an _
    """
    s = os.path.splitext(os.path.basename(s))[0].strip()
    return re.sub('[\s-]+', '_', re.sub('^[^a-zA-Z]+|[^\w\s-]+','', s))


def import_rastermap(fname, layer=''):
    """Import a raster layer into GRASS

    Uses grass_safe to convert filename into a layer name if none is provided.
    @returns string - layer name
    """
    runlog.debug('import_rastermap %s' % fname)

    if not layer:
        layer = grass_safe(fname)

    proj = grass.read_command('g.proj', flags='wf')

    with open(os.devnull, 'wb') as FNULL:
        check_call(['gdalwarp', '-t_srs', proj, fname, 'proj.gtif'], 
                   stdout=FNULL, stderr=subprocess.STDOUT)

    if grass.find_file(layer)['name']:
        grass.run_command('g.remove', flags='f', rast=layer)
    if grass.run_command('r.in.gdal', _input='proj.gtif', output=layer,
            overwrite=True, quiet=True):
        raise RuntimeError('unable to import rastermap ' + fname)

    os.remove('proj.gtif')

    return layer

def clean_fields(sname, fields=('cat', 'cat_', 'CAT', 'CAT_', 'Cat')):
    """remove fields from vector layer

    NOTE: Somewhat convoluted because of OGR design, after the field is 
    deleted the field count becomes invalid.  So the for loop is restarted
    until no more matching fields are found.
    """
    shape = ogr.Open(sname, 1)
    if not shape:
        raise RuntimeError('unable to open projected shapefile')
    layer = shape.GetLayer(0)

    mods = True
    while mods:
        mods = False
        ldef = layer.GetLayerDefn()
        for i in range(ldef.GetFieldCount()):
            if ldef.GetFieldDefn(i).GetName().lower() in fields:
                layer.DeleteField(i)
                mods = True
                break

    # Should call DestroyDataSource but doesn't seem to exist


def import_vectormap(fname, layer=''):
    """Import a vector layer into GRASS.

    Uses grass_safe to convert filename into a layer name if none is provided.

    NOTE: snap and min_area values are hardcoded and may not be appropriate
    for all projects

    @returns string - layer name
    """

    if not layer:
        layer = grass_safe(fname)

    # remove temporary previously projected shape files
    for f in iglob('proj.*'):
        os.remove(f)

    proj = grass.read_command('g.proj', flags='wf')

    check_call(['ogr2ogr', '-t_srs', proj, 'proj.shp', fname])
    clean_fields('proj.shp')

    if grass.run_command('v.in.ogr', flags='w', dsn='proj.shp',
           snap='0.01', output=layer, overwrite=True, quiet=True):
        raise RuntimeError('unable to import vectormap ' + fname)

    for f in iglob('proj.*'):
        os.remove(f)

    return layer


# Note: we currently read the entire uncompressed content of
# a file into a string and then write it to file.  Python 2.6
# provides a mechanssm for reading files piecemeal.
def get_shapefile(url):

    try:
        if url.startswith('file://'):
            z = ZipFile(url.replace('file://',''))
        else:    
            z = ZipFile(site.getURL(url))
    except BadZipfile:
        raise RuntimeError('%s is not zip file' % url)

    # processes each file in the zipfile because embedded
    # directories are also part of the namelist we exclude
    # any filename ending with a trailing slash
    shapefile = None
    for zname in z.namelist():
        if zname.endswith('/'):
            continue
        else:
            fname = os.path.basename(zname)
            if fname.endswith('.shp'):
                shapefile = fname
            with open(fname, 'wb') as f:
                content = z.read(zname)
                f.write(content)

    if not shapefile:
        raise RuntimeError('%s did not contain a shapefile' % url)

    return shapefile

def getPerCellChange(percell, time, start, end=None, mult=1000000.0):
    """Read a percell map and returns the accumulated change over time.

    Args:
      percell (str): GLUC output map such as 'ppcell' or 'empcell'
      time (str): GLUC output map such as 'summary' or 'year'
      start (int): first year of requested time series
      end (int): last year of requested time series, inclusive (default=
        max of <time> map)
      mult (float): multiplier used to process <percell> as int values
        (default=10^6)
      
    Returns:
      list of floats: accumulated change from start to end inclusive.  The
         list is always a delta based on the value of the first element.
    """

    # transformm percell map to fixed-point integer for easier processing
    layer = 'tmp_' + ''.join(random.sample('ABCDEFGHIJKLMNOPQRSTUVWXZY', 8))
    grass.mapcalc('$layer=int($mult*$percell)', layer=layer, percell=percell,
                  mult=mult, quiet=True)
    stats = grass.read_command('r.stats', flags='c', quiet=True,
                               _input='%s,%s' % (time, layer))
    grass.run_command('g.remove', rast=layer, quiet=True)

    ts = {}
    for l in stats.splitlines():
        t,val,count = l.split()
        ts[int(t)]=ts.get(int(t),0.0)+int(val)*int(count)/mult

    if end == None:
        end = max(ts.keys())

    # accumulate results
    # setdefault only
    ts.setdefault(start, 0.0)
    for i in range(start+1, end+1):
        ts[i] = ts[i-1] + ts.get(i, 0.0)

    # always return the delta based on 'start'
    return [ts[i]-ts[start] for i in range(start,end+1)]

def check_extent(layer, parent):

    parent = grass.parse_command('v.info', flags='g', map=parent)
    layer = grass.parse_command('v.info', flags='g', map=layer)

    n = float(layer['north']) <= float(parent['north'])
    s = float(layer['south']) >= float(parent['south'])
    w = float(layer['west']) >= float(parent['west'])
    e = float(layer['east']) <= float(parent['east'])

    return n and s and e and w


def sanity_check(boundary, landcover, nogrowth, density, demand, ratio=0.8):
    """Perform sanity check on subregional zones.

    Creates a developable mask using boundary, landcover, and
    nogrowth layers and apply it to the density map to create a
    sanity (s) layer. The sum of the the sanity layer is the max
    potential development for the region given current constraints.
    If the desired development is greater than the potential for the
    region and an error message is returned with statistics.
    """

    stats = { 'ratio': ratio, 'demand': demand }

    if not demand > 0.0:
        runlog.debug('sanity_check: demand <= 0, should this be an error?')
        return stats
    
    # check the boundary for location, projection, size, etc
    s = grass.parse_command('r.univar', map=boundary, quiet=True,
            parse = (grass.parse_key_val, { 'sep' : ':' }))
    stats['boundary'] = int(s.get('sum', 0))
    if stats['boundary'] < 1:
        runlog.debug('sanity_check: boundary failure')
        stats['fail'] = 'boundary'
        stats['msg'] = 'boundary out of the study region or malformed'
        return stats

    # check the landcover for developable cells
    grass.mapcalc('s=if($b && $lu>29 && $lu<90)', quiet=True,
            b=boundary, lu=landcover)
    s = grass.parse_command('r.univar', map='s', quiet=True,
            parse = (grass.parse_key_val, { 'sep' : ':' }))
    stats['landcover'] = int(s.get('sum', 0))
    if stats['landcover'] < 1:
        runlog.debug('sanity_check: landcover failure')
        stats['fail'] = 'landcover'
        stats['msg'] = str('no appropriate landcover cells (perhaps '
            'the redevelopment flag is set in correctly)')
        return stats

    # check zone and nogrowth overlap
    grass.mapcalc('s=if($b && $ng)', quiet=True,
            b=boundary,ng=nogrowth)
    s = grass.parse_command('r.univar', map='s', quiet=True,
            parse = (grass.parse_key_val, { 'sep' : ':' }))
    stats['nogrowth'] = int(s.get('sum', 0))
    if stats['nogrowth'] == stats['boundary']:
        runlog.debug('sanity_check: nogrowth failure')
        stats['fail'] = 'nogrowth'
        stats['msg'] = str('nogrowth layers overlaps effective zone'
            'inhibiting development)')
        return stats

    # check the boundary, landcover and nogrowth overlap
    grass.mapcalc('s=if($b && $lu>25 && $lu<90 && $ng==0)', quiet=True,
            b=boundary,lu=landcover,ng=nogrowth)
    s = grass.parse_command('r.univar', map='s', quiet=True,
            parse = (grass.parse_key_val, { 'sep' : ':' }))
    stats['developable'] = int(s.get('sum', 0))
    if stats['developable'] < 1:
        runlog.debug('sanity_check: developable failure')
        stats['fail'] = 'developable'
        stats['msg'] = str('no developable cells available (some '
            'interaction of zone, landcover, and nogrowth)')
        return stats

    # check the max development potential
    grass.mapcalc('s=if($b && $lu>25 && $lu<90 && $ng==0, $d, null())',
            b=boundary,lu=landcover,ng=nogrowth,d=density, quiet=True)
    s = grass.parse_command('r.univar', map='s', quiet=True,
            parse = (grass.parse_key_val, { 'sep' : ':' }))
    stats['potential'] = float(s.get('sum', 0))
    if demand > ratio * stats['potential']:
        runlog.debug('sanity_check: potential failure')
        stats['fail'] = 'potential'
        stats['msg'] = 'demand exceeds max potential development'
        return stats
    else:
        stats['mean'] = s.get('mean', 'na')
        stats['maximum'] = s.get('maximum', 'na')
        stats['minimum'] = s.get('minimum', 'na')

    return stats 

def sanity_report(f, title, stats):
    """Writes the results of the sanity check.  Popsane and empsane are
    the results of a r.univar run against the boundary and density maps
    taking into account landcover and nogrowth areas.  Refer to the 
    document for r.univar to determine keys available in popsane/empsane.
    """

    if stats.get('msg', ''):
        f.write("<h4>%s</h4>\n" % title)
        f.write("<p>Error: %s</p>\n" % stats['msg'])
        f.write("<ul>\n")
        f.write("<li>net demand = %f</li>\n" % stats.get('demand', 0.0))

        f.write("<li>cells within boundary = %d</li>\n" \
                % stats.get('boundary', 0))
        f.write("<li>developable landcover cells = %d</li>\n" \
                % stats.get('landcover', 0))
        f.write("<li>no growth cells = %d</li>\n" % stats.get('nogrowth', 0))
        f.write("<li>total developable cells = %d</li>\n" \
                % stats.get('developable', 0))

        f.write("<li>max potential = %f</li>\n" % stats.get('potential',0.0))
        f.write("<li>developable percentage = %d%%</li>\n" \
                % int(100 * stats.get('ratio', 1.0)))
        f.write("<li>available potential = %f</li>\n" \
                % (stats.get('ratio', 1.0) * stats.get('potential', 0.0)))

        if 'mean' in stats.keys():
            f.write("<li>average density = %s</li>\n" % stats['mean'])
        if 'maximum' in stats.keys():
            f.write("<li>max density = %s</li>\n" % stats['maximum'])
        if 'minimum' in stats.keys():
            f.write("<li>min density = %s</li>\n" % stats['minimum'])

        f.write("</ul>\n")


def get_rasters(url):

    try:
        fname = site.saveFile(url)
        z = ZipFile(fname)

    except BadZipfile:
        return [fname, ]

    # TODO fix error handling
    except:
        return []

    rasters = []
    for fname in z.namelist():
        if fname.endswith('/'):
            continue
        else:
            fname = os.path.basename(fname)
            rasters.append(fname)
            with open(fname, 'wb') as f:
                f.write(z.read(fname))

    return rasters


def getLayerAttr(url, attr, null='0'):
    """Get a single shapefile and convert it into a raster mask.  """

    shapefile = get_shapefile(url)
    layer = import_vectormap(shapefile)
    
    grass.run_command('v.to.rast', input=layer, output=layer, 
        column=attr, quiet=True, overwrite=True)
    grass.run_command('r.null', map=layer, null=null)

    return layer


def getLayerMask(url):
    """Get a single shapefile and convert it into a raster mask.  """

    runlog.debug('getLayerMask: ' + url)

    try:
        shapefile = get_shapefile(url)
        layer = import_vectormap(shapefile)
    
        grass.run_command('v.to.rast', input=layer, output=layer, 
                use='val', value='1', quiet=True, overwrite=True)
        grass.run_command('r.null', map=layer, null='0', quiet=True)
    except:
        runlog.error('Error getting effective zone: ' + proj['layer'])
        runlog.exception('getLayerMask failed: ' + proj['layer'])
        sys.exit(3)

    return layer

def import_density(projid, url, colname, default):
    """import vector density map and convert to raster

    The density raster is created by importing a vector layer from
    <url> and rasterizing based on <colname>.  The density map will
    be named <projid>_<colname>.  If <url> is not specified then the 
    <default> regional projection file will be used.

    GRASS:
      <shapefile name> (vector): created
      <projid>_<colname> (raster): created

    Args:
      projid (str): name of the projection (for logging)
      url (str): url to the density map
      colname (str): name of the vector column to be used for rasterizing
      default (str): regional density map to be used if url is not specified
    """

    density = projid + '_' + colname

    # use the regional density
    if not url:
       if grass.run_command('g.copy', rast=[default, density]):
           raise RuntimeError("regional density map '%s' not found" % default)
       else:
           runlog.debug('no url for %s, using %s' % density, default)
           return density

    runlog.debug('importing density map %s (%s)' % (projid, url))

    # import the new density map
    shapefile = get_shapefile(url)
    layer = import_vectormap(shapefile)
    if grass.run_command('v.to.rast', _input=layer, column=colname,
                         output=density):
        raise RuntimeError('unable to rasterize %s from %s (%s)' %
                               (layer, projid, url))

    # convert density acres to cells
    grass.mapcalc('$density=.222*$density', density=density)

    return density


def getTEnetwork(url):
    """getTEnetwork - downloads the TE network, unzips, and imports
       into GRASS.  Utilizes the utility script 'importTEroads' from 
       the projects bin directory.
    """
    runlog.debug('getTEnetwork: importing transportation network')
    script = './bin/importTEroads'
    logname = os.path.basename(script)+'.log'
    print logname

    shapefile = get_shapefile(url)
    check_call('%s "%s" > %s 2>&1' % (script, shapefile, logname), shell=True)


def getSpecialDrivers(urllist):
    """getSpecialDrivers - downloads 0 or more shapefiles, convert
       them to raster and merge into partial probability map.
    """
    runlog.debug('getSepcialDrivers: importing special drivers')
    script = './bin/importSpecials'
    logname = os.path.basename(script)+'.log'

    shplist = []
    for url in urllist:
        shplist.append('"%s"' % get_shapefile(url))

    check_call('%s %s > %s 2>&1' % (script, ' '.join(shplist), logname),
        shell=True)


def getNoGrowthLayers(urllist):
    """getNoGrowthLayers - downloads 0 or more shapefiles, convert
       them to raster and merge into the noGrowth layers
    """
    runlog.debug('getNoGrowthLayers: importing no growth layers')
    script = './bin/importNoGrowth'
    logname = os.path.basename(script)+'.log'

    shplist = []
    for url in urllist:
        shplist.append('"%s"' % get_shapefile(url))

    check_call('%s %s > %s 2>&1' % (script, ' '.join(shplist), logname),
        shell=True)


def getInitialLandcover(url):
    runlog.debug('getInitialLandcover: initial landcover')
    script = './bin/importLU'
    logname = os.path.basename(script)+'.log'

    site.getURL(url, filename="landcover")
    check_call('%s landcover > %s 2>&1' % (script, logname), shell=True)


def getStartingResults(url):
    script = './bin/importStartingResults'
    logname = os.path.basename(script)+'.log'

    rasters = get_rasters(url+'/model_results.zip')
    check_call('%s %s 2> %s' % (script, ' '.join(rasters), logname),
        shell=True)


def cacheProbmaps(drivers):
    """Write the probability maps and uploads them to the Plone site
    for future use.
    """
    runlog.debug('caching probmaps for %s' % drivers['title'])

    grass.run_command('r.out.gdal', _input='probmap_res', 
                      output='probmap_res.gtif', _type='Float32')
    grass.run_command('r.out.gdal', _input='probmap_com', 
                      output='probmap_com.gtif', _type='Float32')
    try:
        cmd = 'zip probmaps.zip probmap_res.gtif probmap_com.gtif'
        check_call(cmd.split())
        site.putProbmapCache(drivers['url'], 'probmaps.zip')
    except Exception:
        runlog.warn('Failed Caching Probmaps')


def buildProbmaps(drivers):
    """Builds a pair of probability maps based on given driver set.
    """
    
    runlog.debug('build probmaps for %s' % drivers['title'])
    dset_id = grass_safe(drivers['id'])

    # always work on the full region
    grass.mapcalc('studyAreaBase=1', quiet=True)
    
    # load DEM layer only once and assume it never changes
    # TODO: If driver not provided used local version
    print "Loading DEM...........\n"
    d = grass.find_file('demBase', element='cell')
    if d['name'] == '':
        try:
            site.getURL(drivers['dem'], filename='dem')
            import_rastermap('dem', layer='demBase')
        except Exception:
            runlog.warn('dem driver not found, checking for local version')
            if os.path.exists('dem.zip'):
                runlog.warn('local demo found, loading as demBase')
                check_call('unzip dem.zip', shell=True)
                import_rastermap('dem.gtif', layer='demBase')
            else:
                runlog.warn('local dem not found, creating blank demBase')
                grass.mapcalc('demBase=float(0.0)')
    

    # imports the necessary road networks
    # NOTE: Truly ugly hack to put a default road network into the process
    # ywkim modified this to make it work
    """
    d = grass.find_file('extra_roads', element='vector')
    # ywkim, if there is no extra road, the [roads] tag will be empty
    # so when the [roads] tag is not there, it will import the pre-exist shapefile.
    # This shapefile could be very small simple segment.
    if d['name'] == '':
        if drivers['roads']:
            shp = get_shapefile(drivers['roads'])
            import_vectormap(shp, layer='extra_roads')
        else:
            import_vectormap('extra_roads.shp', layer='extra_roads')
            grass.run_command('v.db.addcol', map='extra_roads', 
                              column='x integer')
            grass.run_command('v.db.update', map='extra_roads',
                              column='x', value='fclass')
            grass.run_command('v.db.dropcol', map='extra_roads',
                              column='fclass')
            grass.run_command('v.db.renamecol', map='extra_roads',
                              column='x,fclass')
            
    # ywkim changed to accept tdm
    # bin/importTEraods is now accepting the regular road
    getTEnetwork(drivers['tdm'])

    """
    # ywkim added for importing regular roads
    print "Importing road network..............\n"
    runlog.debug('importing road network')
    shp = get_shapefile(drivers['tdm'])
    import_vectormap(shp, layer='otherroads')
    
    
    # employment centers
    print "Importing empcenters..............\n"
    runlog.debug('importing empcenters')
    shp = get_shapefile(drivers['empcenters']['empcenter'])
    layer = import_vectormap(shp, layer='empcentersBase')
    #grass.run_command('v.net', quiet=True, input='extra_roads',
    #        points='empcentersBase', operation='connect', thresh='500')

    # population centers
    print "Importing popcenters.............\n"
    runlog.debug('importing popcenters')
    shp = get_shapefile(drivers['popcenters']['popcenter'])
    layer = import_vectormap(shp, layer='popcentersBase')
    #grass.run_command('v.net', quiet=True, input='extra_roads',
    #        points='popcentersBase', operation='connect', thresh='500')

    # build attractor maps and probability maps
    print "Building attractor maps..............\n"
    runlog.debug('running attmaps.make')
    with open('%s_attmaps.log' % dset_id, 'wb') as log:
        cmd = 'make -f bin/attmaps.make attmaps'
        check_call(cmd.split(), stdout=log, stderr=subprocess.STDOUT)
            
    # create special drivers
    runlog.debug('importing special drivers')
    getSpecialDrivers(drivers.get('specials', []))

    runlog.debug('running probmaps.make')
    with open('%s_probmaps.log' % dset_id, 'wb') as log:
        cmd = 'make -f bin/probmaps.make'
        check_call(cmd.split(), stdout=log, stderr=subprocess.STDOUT)


def writeProbmaps(prefix, year, directory='gluc/Data'):
    """Writes the current probmap_res and probmap_com to the specified
    directory for use by the LUC model.
    """
    runlog.debug('writing probmaps for %s' % year)

    if prefix: prefix += '_'
    if year: year = '_' + year

    resmap = os.path.join(directory, '%sprobmap_res%s.bil' % (prefix, year))
    commap = os.path.join(directory, '%sprobmap_com%s.bil' % (prefix, year))

    grass.run_command('r.out.gdal', quiet=True, input='probmap_res',
            output=resmap, format='EHdr', type='Float32')
    grass.run_command('r.out.gdal', quiet=True, input='probmap_com',
            output=commap, format='EHdr', type='Float32')

def publishProjTable(dest, fname):
    site.putFileURL(fname, dest, type='text/csv',
            title='Detailed Projection Data',)

def publishSimMaps(dest):
    """Save basic results as SimMaps on the portal

    TODO: this should publish a regional boundary map as the base map, and
    set the boundary maps as the default view for the scenario, and finally
    add details to the boundary map with links for model results, etc.
    """

    grass.run_command('r.out.gdal', _input='change', output='change.gtif',
                      _type='Byte', quiet=True)
    url = site.putSimMap('change.gtif', 'results/change.map', dest)
    site.updateSimMap(url, title='Change Map', 
        description='cells with change in population, employment or land use')
    grass.run_command('r.out.gdal', _input='ppcell', output='ppcell.gtif',
                      _type='Float32', quiet=True)
    url = site.putSimMap('ppcell.gtif', 'results/ppcell.map', dest)
    site.updateSimMap(url, title='Population Change', 
        description='cells with change in population')
    grass.run_command('r.out.gdal', _input='empcell', output='empcell.gtif',
                      _type='Float32', quiet=True)
    url = site.putSimMap('empcell.gtif', 'results/empcell.map', dest)
    site.updateSimMap(url, title='Employment Change', 
        description='cells with change in employment')
    grass.run_command('r.out.gdal', _input='year', output='year.gtif',
                      _type='UInt16', quiet=True)
    url = site.putSimMap('year.gtif', 'results/year.map', dest)
    site.updateSimMap(url, title='Year of Change', 
        description='year each cell changed state')


def publishProbmaps(dest):
    """Imports any probabilty maps generated by the model (those stored
    in gluc/DriverOutput/Maps, rewrites them as GTIFs, zips and posts
    them to the resultsdir.

    Note: lots of hardcoded paths and filenames!
    """
    mapdir = 'gluc/DriverOutput/Maps'
    pmaps = ['initial_probmap_res', 'initial_probmap_com', 
             'final_probmap_res', 'final_probmap_com']
    layers = []
    for p in pmaps:
        fname = os.path.join(mapdir, p)+'.asc'
        if os.path.exists(fname):
            grass.run_command('r.in.gdal', flags='o', input=fname, output=p, 
                              quiet=True, overwrite=True)
            layers.append(p)
    if len(layers) > 0:
        for p in layers:
            grass.run_command('r.out.gdal', flags='c', input=p,
                    output=p+'.gtif', quiet=True, overwrite=True)
            check_call(['zip', 'probmaps.zip', p+'.gtif'])
        site.putFileURL('probmaps.zip', dest, title='Probability Maps')

def publishResults(dest):
    """Outputs standard maps (ppcell, hhcell, empcell, change, and year)
    as a GTIFs, zips them up, and posts them to the resultsdir.
    """

    grass.run_command('r.out.gdal', input='change',
            output='change.gtif', type='Byte', quiet=True)
    grass.run_command('r.out.gdal', flags='c', input='ppcell',
            output='ppcell.gtif', type='Float32', quiet=True)
    grass.run_command('r.out.gdal', flags='c', input='hhcell', 
            output='hhcell.gtif', type='Float32', quiet=True)
    grass.run_command('r.out.gdal', flags='c', input='empcell', 
            output='empcell.gtif', type='Float32', quiet=True)
    grass.run_command('r.out.gdal', flags='c', input='year', 
            output='year.gtif', type='UInt16', quiet=True)
    check_call(['zip', 'model_results.zip', 'ppcell.gtif', 'hhcell.gtif',
            'empcell.gtif', 'year.gtif', 'change.gtif'])

    site.putFileURL('model_results.zip', dest, title='Model Results')


def get_location(uri, user, password, fname='grass.zip'):
    """get the empty GRASS location

    Args:
      uri (str): URL for download
      user (str): portal user
      password (str): portal password
      fname (str): tmp name for the GRASS location
    """

    r = requests.get(uri, auth=(user, password), stream=True)
    r.raise_for_status()

    with open(fname, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            f.write(chunk)

    if r.headers.get('content-type').startswith('application/zip'):
        with open(os.devnull, 'wb') as FNULL:
            check_call(['unzip', '-o', fname], 
                        stdout=FNULL, stderr=subprocess.STDOUT)


def get_config(uri, user, password, fname='config.xml'):
    """get the configuration from any one of multiple sources
 
    Args:
      uri (str): URL or file name or - for stdin
      user (str): portal user 
      password (str): portal password
      fname (str): name of the config file to be written
    """

    if uri == '-':
        config = sys.stdin.read()

    elif uri.startswith('http'):
        r = requests.get(uri, auth=(user, password))
        r.raise_for_status()
        config = r.text

    elif os.path.exists(uri):
        with open(uri) as f:
            config = f.read()

    else:
        raise RuntimeError('configuration information not found')

    with open(fname, 'wb') as f:
        f.write(config)

    return config


def main():

    jobstart = time.asctime()

    os.environ['PATH'] = ':'.join(['./bin', os.environ.get('BIN', '.'),
                                   '/bin', '/usr/bin'])

    usage = "Usage: %prog [options] arg"
    parser = OptionParser(usage=usage, version='%prog')
    parser.add_option('-c', '--config', metavar='FILE', default='-',
        help='configuration FILE (default=stdin)')
    parser.add_option('-b', '--breakpoint', default=False, action='store_true',
        help='set a breakpoint at the normal place')
    parser.add_option('-p', '--nopost', default=False, action='store_true',
        help='terminates after model results posted, no post-processing.')
    parser.add_option('-l', '--local', default=False, action='store_true',
        help='runs locally, no information posted the planning portal')
    parser.add_option('-U', '--user', default=None,
        help='Portal user name (or PORTAL_USER environmental var)')
    parser.add_option('-X', '--password', default=None,
        help='Portal password (or PORTAL_PASSWORD environmental var)')

    (options, args) = parser.parse_args()


    # invoke the debugger if requested from the command line
    if options.breakpoint:
        import pdb; pdb.set_trace()

    # check for user and password
    user = options.user or os.environ.get('PORTAL_USER', '')
    password = options.password or os.environ.get('PORTAL_PASSWORD', '')
    if not user or not password:
        sys.stderr.write('User and password information is required. '
                'Please set using command line or environmental variables.\n')
        raise ValueError('user and password required.')

    # parse the configuration file
    print "Parsing configuration file.............\n"
    config = get_config(options.config, user, password)
    luc = LUC(config)

    # grab some useful values from the config file
    # title = human-readable name of the scenario
    # scenario = unique name of the scenario (also used as grass mapset)
    # resultsdir = URL of scenario folder in plone
    title = luc.scenario['title']
    scenario = luc.scenario['id']
    resultsdir = luc.scenario['results']

    # setup the GRASS environment
    print "Setting up GRASS environment.............\n"
    get_location(luc.scenario['grass_loc'], user, password)
    grass_config('grass', 'model')

    # conection to the portal 
    global site
    site = LEAMsite(resultsdir, user=user, passwd=password)

    # create model run log file on the site that is updated dynamically
    global runlog
    runlog = RunLog(resultsdir, site, initmsg='Scenario ' + title)
    runlog.p('started at '+jobstart)

    # maintains target and actual projections
    global ptable 
    ptable = ProjTable()

    # create results raster layers
    print "Creating result raster layers.............\n"
    runlog.debug("Initializing GRASS model layers with 'gluc.make start'")
    cmd = 'make -f ./bin/gluc.make start'
    with open('gluc_make_start.log', 'w') as log:
        check_call(cmd.split(), stdout=log, stderr=subprocess.STDOUT)

    # process growth projections
    print "Processing growth projections.............\n"
    growth = dict(deltapop=[0.0], deltaemp=[0.0])
    if luc.growth:

        print "Building probability maps from growth driver sets.............\n"
        runlog.h('Building Probability Maps From Growth Driver Sets')
        startyear = processDriverSets(luc.growthmap, prefix='growth')

        # filter out regional projection from growth projections
        runlog.h('Processing Growth Projections')
        subregional, regional = filter_regional_projection(luc.growth)
        create_regional_densities(regional)
        growth = processProjections('growth', subregional, startyear)

    # SANITY -- check to see if sanity report was produced
    if os.path.exists('sanity.htm'):
        runlog.error('Sanity Checks Failed')
        runlog.error('Scenario Terminated - check sanity report')
        with open('sanity.htm') as f:
            site.putDocument(f, resultsdir, 'Sanity Check Report')
        sys.exit(2)

    # process driver sets associated with vacancy
    # TODO: the startyear may not match the growth causing problems 
    #  when merge deltapop/deltaemp from growth and decline into regional
    print "Processing driver sets associated with vacancy.............\n"
    decline = dict(deltapop=[0.0], deltaemp=[0.0])
    if luc.decline:

        if luc.declinemap:
            runlog.h('Building Probability Maps From Vacancy Driver Sets')
            sy = processDriverSets(luc.declinemap, prefix='decline')
    
        else:
            runlog.error('No vacancy driver sets given even though '
                         'vacancy projections were specified.')
            runlog.h('Model Run Ended Prematurely')
            sys.exit(3)
    
        runlog.h('Processing Vacancy Projections')
        decline = processProjections('decline', luc.decline, sy)


    # REGIONAL -- execute for regional models
    # TODO: you can't have more than one regional why keep it as a list?
    print "Executing regional models.............\n"
    for proj in regional:
        projid = grass_safe(proj['id'])
        mode = proj.get('mode','') or 'regional'
        runlog.h('Starting Regional Projection -- %s' % proj['title'])

        # reads target demand graph, subtracts results from previous
        # growth and decline projections and write an adjusted demand.graphs
        print "Reading demand graph............."
        runlog.debug('creating regional demand')
        startyear = int(growth['startyear'])
        endyear = int(proj['endyear'])
        ptable.years(projid, mode, startyear, endyear)

        demand = site.getURL(proj['graph']).getvalue()

        pop = getDemandGraph(demand, ['population'], start=startyear)
        ptable.population(projid, mode, 'target', pop)
        pop = [(x[0], x[1]-x[2]-x[3]) for x in zip(
                range(startyear,endyear+1), pop, 
                repeat_last(growth['deltapop']),
                repeat_last(decline['deltapop']))]
        ptable.population(projid, mode, 'adjusted', [p[1] for p in pop])

        emp = getDemandGraph(demand, ['employment'], start=startyear)
        ptable.employment(projid, 'regional', 'target', emp)
        emp = [(x[0], x[1]-x[2]-x[3]) for x in zip(
                range(startyear,endyear+1), emp, 
                repeat_last(growth['deltaemp']),
                repeat_last(decline['deltaemp']))]
        ptable.employment(projid, mode, 'adjusted', [e[1] for e in emp])

        writeDemand(proj['title'], pop, emp)

        # output the boundary map
        print "Outputting the boundary map.............\n"
        boundary = proj.setdefault('boundary', getLayerMask(proj['layer']))
        grass.run_command('r.out.gdal', input=boundary, 
            output='gluc/Data/boundary.bil', format='EHdr', type='Byte')

        # rewrites the landcover map
        print "Rewriting the landcover map.............\n"
        grass.run_command('r.out.gdal', _input='landcoverBase',
            output='gluc/Data/landcover.bil', _format='EHdr', _type='Byte')

        # add growth zones to nogrowth layer
        print "Adding growth zones to nogrowth layer.............\n"
        runlog.debug('regional nogrowth processing')
        d = grass.find_file('subzones', element='vector')
        if d['name'] == '':
            runlog.debug('no subzones layer found')
            grass.run_command('r.out.gdal', _input='nogrowth', 
                output='gluc/Data/nogrowth.bil', _format='EHdr', _type='Byte')
        else:
            runlog.debug('merging subzones layer found')
            grass.mapcalc('ng=if(nogrowth || subzones, 1, 0)')
            grass.run_command('r.out.gdal', _input='ng', 
                output='gluc/Data/nogrowth.bil', _format='EHdr', _type='Byte')
            grass.run_command('g.remove', rast='ng')

        # ensure the projection density maps match both the _density layer
        # and the .bil file.
        grass.run_command('g.copy', rast='regional_popdens,pop_density')
        grass.run_command('g.copy', rast='regional_empdens,emp_density')
        grass.run_command('r.out.gdal', _input='pop_density', 
            output='gluc/Data/pop_density.bil', _type='Float32',_format='EHdr')
        grass.run_command('r.out.gdal', _input='emp_density', 
            output='gluc/Data/emp_density.bil', _type='Float32',_format='EHdr') 

        writeConfig(confname=projid, prefix='growth_', 
                    start=startyear, end=endyear)
        executeModel(projid, 'growth', startyear)

        # extract the time series change in pop and emp from the model run
        print "Extracting the time series change............."
        pop,emp = getProjectionTimeSeries(proj, projlen=endyear-startyear+1)
        ptable.population(projid, mode, 'actual', pop)
        ptable.employment(projid, mode, 'actual', emp)

        runlog.h('Regional Model Complete')

    # log that no regional model has been found
    if not regional:
        runlog.warn('No Regional Model Found')
        runlog.p('The basic results will be posted but some post-processing '
                 '(section maps, taz data, etc.) will not be generated. ')

    if options.local:
        runlog.debug('running in local mode, no results posted')
        ptable.write_csv(filename='projections.csv')
    else:
        runlog.h('Posting Results')
        ptable.write_csv(filename='projections.csv')
        publishProjTable(resultsdir, 'projections.csv')
        publishSimMaps(resultsdir)
        publishResults(resultsdir)
        publishProbmaps(resultsdir)

    # Runs the model without posting results
    print "running the model without posting results.............\n"
    if options.local or options.nopost:
        runlog.debug('no post-processing requested on command line')

    else:
        runlog.h('Post-processing jobs queued')
        site.getURL(resultsdir + '/queue_post')


if __name__ == "__main__":

    try:
        main()    

    # Uncaught or re-raised error from main
    except Exception as e:
        if 'runlog' in globals():
            runlog.error(str(e))
            runlog.exception('main() exits with exception')
            runlog.error('Scenario Terminated')
            sys.exit(1)

        # runlog has not be initialized, use default error handling
        else:
            raise

    # successful termination
    runlog.h('Scenario Completed Successfully at %s.' % time.asctime())
    sys.exit(0)
