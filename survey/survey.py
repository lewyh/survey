"""
Terminology:
survey is a collection of single-band exposures, 
which are arbitrarly grouped into "fields".

Module conventions
- use ra/dec as decimal degrees OR DIE
- give timestamps as "YYYY-MM-DDTHH:mm:ss" 
(appended, if necessary, with ".milliseconds")

"""
import numpy as np


class Survey:

    def __init__(self, name):
        self.name = name


    def get_pointing_strategy(self):
        """Return numpy.recarray with one row for each planned pointing."""
        pass

    def get_fields(self):
        """Return a numpy.recarray containing all the metadata of fields."""
        raise NotImplementedError("Survey is an abstract class!")





class IPHAS(Survey):

    def __init__(self):
        Survey.__init__(self, "IPHAS")

    def get_fields(self):
        fieldlist = []
        for i in range (0,10):
            fieldlist.append( Field(i) )
        return fieldlist








