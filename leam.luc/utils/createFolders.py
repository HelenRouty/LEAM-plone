import os, sys
import optparse

from leamsite import LEAMsite


def main():

    usage = "usage: %prog [options] <site URL>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-u", "--user", 
            default=os.environ.get('PORTAL_USER', ''),
            help="Plone user")
    parser.add_option("-p", "--password",
            default=os.environ.get('PORTAL_PASSWORD', ''),
            help="Plone user's password")

    (opts, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("the URL to the Plone site is required")

    url = args[0]
    site = LEAMsite(url, user=opts.user, passwd=opts.password)
    if site.error:
        parser.error("the URL is not a valid site")

    top = site.createFolder("luc", url)
    site.editFolder(top, 
        title="Land Use Model",
        description="LEAM Land Use Change Model allows future land use "
            "scenarios to be created and evaluated.",
    )

    scenarios = site.createFolder("scenarios", top)
    site.editFolder(scenarios,
        title="Scenarios",
        description="Define and review scenarios in this folder.  New "
            "scenarios will automatically be run and results returned by "
            "the modeling system."
    )

    projections = site.createFolder("projections", top)
    site.editFolder(projections, 
        title="Projections",
        description="Enter population and employment projection associated "
            "with specific areas in this folder.  The projection consist of "
            "the projection rate by year, a region or zone, and population "
            "and employment density maps."
    )

    subregional = site.createFolder("subregional", projections)
    site.editFolder(subregional,
        title="Subregional Maps",
        description="Subregional maps identify different zones used within "
            "the model.  These maps can be used as part of a projection or "
            "within impact models."
    )

    density = site.createFolder("density", projections)
    site.editFolder(density,
        title="Density Maps",
        description="Density maps associated with projections.  Maps "
            "should include POPDENS field, EMPDENS field, or both."
    )

    drivers = site.createFolder("drivers", top)
    site.editFolder(drivers,
        title="Regional Drivers",
        description="Enter a set of drivers that will be associated with "
            "a specific probability map in this folder.  The actual "
            "probabilty map will be created during the model run."
    )

    transportation = site.createFolder("transportation", drivers)
    site.editFolder(transportation,
        title="Transportation Networks",
        description="Transportation networks require two fields, FCLASS "
            "and MINSPEED.  FCLASS is the function class of the road.  "
            "MINSPEED represents the calculated speed at peak traffic times."
    )

    specials = site.createFolder("specials", drivers)
    site.editFolder(specials,
        title = "Special Drivers",
        description="Special drivers provides a mechanism for directly "
            "modifying the probability maps. "
    )
    
    nogrowth = site.createFolder("nogrowth", drivers)
    site.editFolder(nogrowth,
        title = "No Growth Maps",
        description = "No growth layers are used to remove areas from "
            "development. No special fields are required for this layer. "
            "Any areas identified in 'no growth' layers will be ignored "
            "by the model."
    )

    attractors = site.createFolder("attractors", drivers)
    site.editFolder(attractors,
        title="Regional Attractors",
        description="Enter regional attractors such as cities and employment "
            "centers in this folder. The cities layer is a point layer and "
            "must have provide the population in field POP.  The employment "
            "layer should have the number of employees associated with each "
            "employment center in the EMP field."
    )

    grids = site.createFolder("grids", drivers)
    site.editFolder(grids,
        title="Raster Data Layers",
        description="""Land use maps, DEMs, and other raster data types."""
    )

    post = site.createFolder("post-processing", top)
    site.editFolder(post,
        title="Post-Processing",
        description="Items placed in this folder will be executed "
            "automatically when a new LUC scenario has be created. "
    )

    resources = site.createFolder("resources", top)
    site.editFolder(resources,
        title="Resources",
        description="Resources useful during the modeling process."
    )

if __name__ == "__main__":
    main()
