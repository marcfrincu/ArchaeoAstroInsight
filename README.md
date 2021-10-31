# ArchaeoAstroInsight

ArchaeoAstroInsight (A2i) is a Python script developed by Roxana Ionescu and currently maintained by Marc Frincu. It was initially a BSc final year project proposed and supervised by Marc at the West University of Timisoara, Romania. The icons and logo have been designed by Teodora Marisescu. It is designed to be used in the [QGIS platform](https://www.qgis.org/en/site/) to **automate the initial archaeoastronomy analysis researchers perform on archaeological sites** by using Google Earth. The script relies on [www.HeyWhatsThat.com](http://heywhatsthat.com/)  and [SkyScapeR](https://s3-eu-west-2.amazonaws.com/skyscape-archaeology/vignette.html) to calculate the altitude of the horizon in a given azimuth direction. In addition, it uses the [Yale Bright Star Catalog](http://tdc-www.harvard.edu/catalogs/bsc5.html) to identify potential stars in the direction of the orientation.

After configuring the parameters and entering location of the site, the user can draw a line by selecting 2 points. A2i will **automatically compute the azimuth, altitude, and declination of the bearing**. In addition, **it identifies if the bearing points to major lunar and solar points** (solstices, lunastices, equinoxes) and **if any bright stars rise from its direction**. A2i assumes an error of ±0.5°, which is roughly the same as that of a visual observer.

The user manual can be found in the repository.

