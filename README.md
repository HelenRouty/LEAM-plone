**LEAM has four essential parts.**

1. The probability map computation using the driver set input maps.
   * One core function is multicost function in grass.
   * One core function is caculation of centers' attractiveness, and its code is in cities.py that is called by attmap.make.
   * The codes are called from startup.py and exist in attmap.make and probmap.make.
   * The codes are copies from previous LEAM svn.

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
