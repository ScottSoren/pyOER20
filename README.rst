pyOER20
=======
Data and analysis for Scott and Rao et al, 2020
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This repository will get the data analysis etc for the DTU-MIT RuO2 project under version control.
It will expand build on EC_MS (https://pypi.org/project/EC-MS/), and serve to develop some ideas for ixdat (https://ixdat.readthedocs.io/.


Data structures correspond roughly to folders:

- Results will be stored primarily in TOFs.
- I haven't figured out what to do with the "data" folder. I worry that putting in all the pickles would make it too big.
- The samples folder will contain references to the relevant datasets and capacitances.
- TOF series will make the final plots and calculate those damn slopes.

This will not be the relational database I was hoping to make, which would take way long and will be much better when done collaboratively on ixdat.
But it will help me work out the details, while finally helping Reshma finish this 2-year-old project.

Let's get to it!
