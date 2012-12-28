lastfm_queue - Rhythmbox's dynamic queue based on LastFM recommendations.
========================================================================

This plugin is a port from Alexandre Rosenfeld's plugin, to support the new Rhythmbox 2.x plugin architecture.

This plugin will give you the posibility of dinamically build up your playing queue, based on the songs being played. 
Each time Rhythmbox plays a new song, the plugin will look for recommendations from LastFM, randomly choose from the songs you have on your library (that match the given recommendations) and add them to the current playing queue. 

All you gotta do is activate it from the toolbar :]

Installation
-----------
To install, just execute the install.sh script; this will install the plugin locally by default. 
If you want to install the plugin globally (for all the users of the system) you need to use the '-g' option.

Use
---
This plugins doesn't need further configuration after enabling it. Just activate it and enjoy.

**Note:** this plugins makes queries against rhythmbox's database. In **32 bit systems** there's a know bug that doesn't allow plugins writen in python to do just that **without crashing.** 

Contact
------
You can let me know of any bugs or new features you want to see implemented through this repository's issue tracker.
Also, feel free to contact me at my personal email account: asermax at gmail dot com.

And if you feel really friendly, add me on LastFM! My user over there is also asermax :]
