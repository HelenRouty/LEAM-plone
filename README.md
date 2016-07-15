The initial commit is the source code of the current running LEAM on plone written
by previous LEAM programmers.


**LEAM has three essential parts.**
1. The probability map computation using the driver set input maps.
   * One core function is multicost function in grass.
   * One core function is caculation of centers' attractiveness, and its code is in cities.py that is called by attmap.make.
   * The codes are called from startup.py and exist in attmap.make and probmap.make.
   * The codes are copies from previous LEAM svn.
2. The year change map computation using the projection set inputs with probability maps.  
   * The core function is gluc model in this folder.
   * The codes are called from gluc.make in startup.py.
   * The codes are cloned from the LEAMgroup github page.
3. The connection to plone website and the automation process to connect the models.
   * One core function is gluc.simmap to enable colored maps to overlay onto google maps.
   * One core function is leamsite.py which contains interfaces to communicate with Plone.
   * The codes are in this folder which is selectedly copied from currently running LEAM portal web server.
