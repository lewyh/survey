"""
Terminology:
survey is a collection of single-band exposures, 
which are arbitrarly grouped into "fields".

Module conventions
- use ra/dec as decimal degrees OR DIE
- give timestamps as "YYYY-MM-DDTHH:mm:ss" 
(appended, if necessary, with ".milliseconds")

"""
from astropy.io import fits, ascii
import pkg_resources as pkg
import numpy as np
import os

datadir = os.path.realpath(pkg.resource_filename('survey', 'data'))

class Survey:

    def __init__(self, name):
        self.name = name

    def get_pointing_strategy(self):
        """Return numpy.recarray with one row for each planned pointing."""
        self.strategy = fits.getdata(datadir+'/'+self.name+'_strategy.fits',1)
        return

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

class VPHAS(Survey):

    def __init__(self):
        Survey.__init__(self, "VPHAS")

    def download_dqc(self):
        """Downloads the VPHAS dqc files to the package data directory.
        These need to be downloaded seperately due to password protection.
        The files should (hopefully) be updated regularly (monthly?).
        Otherwise download the merged binaries, create your own stats files,
        and refer to them explicitly or place them in the data directory."""
        import urllib2
        import getpass
        domain = "http://star.herts.ac.uk/~hfarnhill/vphas/"
        fields="fields_observed.dat"
        stats_red = "stats-red.fits"
        stats_blu = "stats-blu.fits"
        files = [fields, stats_red, stats_blu]
        username = raw_input("Username: ")
        password = getpass.getpass()
        for f in files:
            try:
                passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
                passman.add_password(None, domain+f, username, password)
                authhandler = urllib2.HTTPBasicAuthHandler(passman)
                opener = urllib2.build_opener(authhandler)
                urllib2.install_opener(opener)
                file_data = urllib2.urlopen(domain+f)
            except urllib2.HTTPError:
                print "Unable to connect, please ensure you "
                print "enter the correct username/password."
                return
            local_file = open(datadir+"/"+f, "w")
            local_file.write(file_data.read())
            local_file.close()
        return

    def observed_red(self, table=None):
        """Convenience function for reading fields observed in red filters"""
        self.observed_fetch(table, red=True, blu=False)

    def observed_blu(self, table=None):
        """Convenience function for reading fields observed in blue filters"""
        self.observed_fetch(table, red=False, blu=True)

    def observed_fetch(self, table=None, red=True, blu=True):
        """Read a fields_observed.dat file and save the contents.

        Arguments to be passed:
            table (default=None) : path of fields_observed file - default
                                   behaviour is to look in package data 
                                   directory for fields_observed.dat.
            red (default=True)   : boolean which when true specifies that
                                   details of the red concats should be read.
            blu (default=True)   : boolean which when true specifies that
                                   details of the blue concats should be read.
        """
        # Ensure date columns always read in as strings - makes it 
        # possible to validate values that are empty against "".
        conv = {"Hari_dat" : [ascii.convert_numpy(np.str)],
                "ugr_dat" : [ascii.convert_numpy(np.str)]}
        if table==None:
            try:
                self.observed = ascii.read(datadir+'/fields_observed.dat', 
                                        converters=conv)
            except:
                print ("Error: No table specified, and no " 
                       "fields_observed.dat")
                print "       in module data directory."
                return 0
        else:
            self.observed = ascii.read(table, converters=conv)
        self.bool_red = red
        self.bool_blu = blu
        return

    def _metadata_fetch(self, colour, directory=None):
        """Read in metadata of fields observed in a concatenation.
        If no directory to metadata files (stats-*.fits) is supplied, 
        assumes that they exist in the module data directory."""
        # Identify relevant string for concatenation.
        if colour=='red':
            concat='Hari'
        elif colour=='blu':
            concat='ugr'
        # If no directory supplied, default to package data directory.
        if directory==None:
            d = datadir
        else:
            d = directory
        # Try to open the stats file, throw an error if no file is found.
        try:
            statsfile = fits.getdata(d+'/stats-'+colour+'.fits', 1)
        except IOError:
            print "No stats-*.fits files present in package data directory, "
            print "and no (or incorrect) directory supplied. Please specify"
            print "where metadata files are located"
            return 0
        # If stats file has been opened, mask out fields that are not
        # present in the fields_observed file.
        mask = np.where(self.observed[concat+'_dat']!="")
        relevant = []
        for i in mask[0]:
            fieldname = str(self.observed['Field'][i])+'-'+\
                        str(self.observed[concat+'_dat'][i])+'-'+colour+'.fits'
            relevant.append(np.where(statsfile['Filename']==fieldname)[0][0])
        return statsfile[relevant]

    def read_metadata(self, directory=None, quick=False):
        """Return numpy.recarrays containing the metadata of fields.
        Accepts argument:
            directory (default=None) : directory that contains the 
                                       stats-*.fits files that contain the 
                                       metadata to read in. Defaults to the 
                                       package data directory.
            quick (default=False)    : boolean that when True allows this 
                                       function to read in fields_observed.dat
                                       from the package data directory.
        NOTE: Unless quick=True has been specified, observed_fetch() should 
        be run before calling this function."""
        if quick==True:
            if self.observed_fetch() == 0:
                print "NOTE:"
                print "     quick=True will only work if the file "
                print "     fields_observed.dat exists in the package "
                print "     data directory"
                return
        else:
            # Need to check that boolean red/blu flags have been 
            # initialized. If not then this is a sign that observed()
            # has not been called, so script will not know which 
            # fields' metadata to read.
            try:
                getattr(self, 'bool_red')
            except:
                print "    Please run observed_fetch() to populate list of "
                print "    observed fields, or provide set quick=True to use "
                print "    fields_observed.dat in the package data directory."
                return
        if self.bool_red==True: 
            metadata_red = self._metadata_fetch('red', directory)
            if metadata_red==0:
                return 
            else:
                self.metadata_red = metadata_red
        if self.bool_blu==True:
            metadata_blu = self._metadata_fetch('blu', directory)
            if metadata_blu==0:
                return 
            else:
                self.metadata_blu = metadata_blu
        return
