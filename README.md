LEAM composition
================
**LEAM has four essential parts.**

1. The probability map computation using the driver set input maps.
   * One core function is multicost function in grass.
   * One core function is caculation of centers' attractiveness, and its code is in cities.py that is called by attmap.make.
   * The codes are called from startup.py and exist in attmap.make and probmap.make.
   * The codes can be copies from previous LEAM svn: portal.leam.illinois.edu/svn/chicago.

2. The year change map computation using the projection set inputs with probability maps.  
   * The core function is gluc model in this folder.
   * The codes are called from gluc.make in startup.py.
   * The codes are cloned from the LEAMgroup github page.

3. The plone website settings.
   * One core function is gluc.simmap to enable colored maps to overlay onto google maps.
   * One core function is leamsite.py which contains interfaces to communicate with Plone.
   * The codes are in this folder which is selectedly copied from currently running LEAM portal web server.
   * Clear plone installation/run/stop instructions are written in 

4. The job supervising model to send plone requests on the job server's startup.py.
   * The core function is leampoll.py and supervisor software.
   * The codes are cloned from the LEAMgroup github page's job monitor.
   * Clear leampoll installation/run/stop instructions are written in this folder.

LEAM Installation
=================
** Note that the instructions below are copied from LEAMgroup github LEAM folder **

1. Install development environment (compilers, mpi, git, various python modules, etc) since we'll need to be able to compile things. I don't have a canonical list of dependancies.

  * `sudo apt-get update` 
  * `sudo apt-get install build-essential autoconf automake git`
  * `sudo apt-get install python-dev python-pip python-gdal` 
  * `sudo pip install requests`

2. Install GIS tools. Primarily GRASS and GDAL, you'll need the development environment too. Looks like the most recent Ubuntu support them as packages which will make things easier.

  * `sudo apt-get install grass grass-doc grass-dev`

3. Clone GRASS modules from the grass-modules repository. There are some script modules and some that need to be compiled with GRASS environment. Then these need to be installed or placed in the path.

4. Clone GLUC from the gluc repository, build, and copy the binary to `/usr/local/bin`. It will need to have an MPI compiler installed to build it.

5. Clone LEAM from the leam repository. A this stage you should be able to run the LEAM model using the sample configuration file provided. This configuration will pull the required data from LEAMgroup servers and run a simple scenario. Results will be stored locally as part of the GRASS mapset rather being pushed back to LEAMgroup.

6. (optional) If the LEAM model will be run automatically using the LEAMgroup Planning Portal front-end then clone the job monitor from for the job-monitory repository and install it.
