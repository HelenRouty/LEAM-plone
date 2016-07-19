grass-modules
=============

Custom grass modules can be built by downloading into the GRASS source build folders.  A better alternative is to use the  g.extension command (and the ever so handy GitHub Subversion support) using the something like the following:
```
g.extension extension=r.multicost svnurl=https://github.com/LEAMgroup/grass-modules/trunk
```
