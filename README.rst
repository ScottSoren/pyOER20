pyOER20
=======
Data and analysis for Scott and Rao et al, 2020
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This repository will get the data analysis etc for the DTU-MIT RuO2 project under version control. It can also be used to open-source the data and analysis when we publish.

Tools in src will expand and build on EC_MS (https://pypi.org/project/EC-MS/), and serve to develop some ideas for ixdat (https://ixdat.readthedocs.io/).

Data structures correspond roughly to folders:

- Measurement metadata (including path on Soren's computer to raw data) will be stored in measurements/
- Results will be stored primarily in the folder TOFs/.
- The samples folder will contain metadata grouping the measurements.
- Figures will store the code to make the figures and the relevant raw data

This will not be the relational database I was hoping to make, which would take way long and will be much better when done collaboratively on ixdat.
But it will help me work out the details, while finally helping Reshma finish this 2-year-old project.

Let's get to it!
