#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

'''
Created on Jun 16, 2015

:author: Eric C. Pellegrini
'''

import cPickle
import glob
import optparse
import os
import subprocess               
import sys

from MDANSE.Core.Error import Error
from MDANSE import ELEMENTS, PLATFORM, REGISTRY
from MDANSE.Framework.Jobs.JobStatus import JobState

class CommandLineParserError(Error):
    pass

class CommandLineParser(optparse.OptionParser):
    '''A sublcass of OptionParser.
    
    Creates the MDANSE commad line parser.
    '''
    
    def add_mmtk_definition(self, option, opt_str, value, parser):
        
        if len(parser.rargs) != 3:
            raise CommandLineParserError("Invalid number of arguments for %r option" % opt_str)
        
        from MDANSE.Framework.MMTKDefinitions import MMTK_DEFINITIONS
        
        MMTK_DEFINITIONS.add(*parser.rargs)
        
        MMTK_DEFINITIONS.save()

    def check_job(self, option, opt_str, value, parser):
        '''Display the jobs list
            
        @param option: the option that triggered the callback.
        @type option: optparse.Option instance
        
        @param opt_str: the option string seen on the command line.
        @type opt_str: str
    
        @param value: the argument for the option.
        @type value: str
    
        @param parser: the MDANSE option parser.
        @type parser: instance of MDANSEOptionParser
        '''

        if len(parser.rargs) != 1:
            raise CommandLineParserError("Invalid number of arguments for %r option" % opt_str)
        
        basename = parser.rargs[0]
        
        filename = os.path.join(PLATFORM.temporary_files_directory(),basename)
        
        if not os.path.exists(filename):
            raise CommandLineParserError("Invalid job name")
            
        # Open the job temporary file
        try:
            f = open(filename, 'rb')
            info = cPickle.load(f)
            f.close()
            
        # If the file could not be opened/unpickled for whatever reason, try at the next checkpoint
        except:
            raise CommandLineParserError("The job %r could not be opened properly." % basename)

        # The job file could be opened and unpickled properly
        else:
            # Check that the unpickled object is a JobStatus object
            if not isinstance(info,JobState):
                raise CommandLineParserError("Invalid contents for job %r." % basename)
            
            print "Information about %s job:" % basename
            for k,v in info.iteritems():            
                print "%-20s [%s]" % (k,v)

    def display_element_info(self, option, opt_str, value, parser):        
    
        if len(parser.rargs) != 1:
            raise CommandLineParserError("Invalid number of arguments for %r option" % opt_str)
        
        element = parser.rargs[0]
                
        try:
            print ELEMENTS.info(element)
        except ValueError:
            raise CommandLineParserError("The entry %r is not registered in the database" % element)
        
    def display_jobs_list(self, option, opt_str, value, parser):
        '''Display the jobs list
            
        @param option: the option that triggered the callback.
        @type option: optparse.Option instance
        
        @param opt_str: the option string seen on the command line.
        @type opt_str: str
    
        @param value: the argument for the option.
        @type value: str
    
        @param parser: the MDANSE option parser.
        @type parser: instance of MDANSEOptionParser
        '''

        if len(parser.rargs) != 0:
            raise CommandLineParserError("Invalid number of arguments for %r option" % opt_str)

        jobs = [f for f in glob.glob(os.path.join(PLATFORM.temporary_files_directory(),'*'))]
                                               
        for j in jobs:

            # Open the job temporary file
            try:
                f = open(j, 'rb')
                info = cPickle.load(f)
                f.close()
                
            # If the file could not be opened/unpickled for whatever reason, try at the next checkpoint
            except:
                continue

            # The job file could be opened and unpickled properly
            else:
                # Check that the unpickled object is a JobStatus object
                if not isinstance(info,JobState):
                    continue
                
                print "%-20s [%s]" % (os.path.basename(j),info["state"])

    def display_trajectory_contents(self, option, opt_str, value, parser):
        '''Displays trajectory contents
            
        @param option: the option that triggered the callback.
        @type option: optparse.Option instance
        
        @param opt_str: the option string seen on the command line.
        @type opt_str: str
    
        @param value: the argument for the option.
        @type value: str
    
        @param parser: the MDANSE option parser.
        @type parser: instance of MDANSEOptionParser
        '''
                
        trajName = parser.rargs[0]
        inputTraj = REGISTRY["input_data"]["mmtk_trajectory"](trajName)
        print inputTraj.info()
       
       
    def error(self, msg):
        '''Called when an error occured in the command line.
        
        @param msg: the error message.
        @type msg: str
        '''
        
        self.print_help(sys.stderr)
        print "\n"
        self.exit(2, "Error: %s\n" % msg)
    

    def query_classes_registry(self, option, opt_str, value, parser):
        '''
        Callback that displays the list of the jobs available in MDANSE
        
        @param option: the Option instance calling the callback.
        
        @param opt_str: the option string seen on the command-line triggering the callback
        
        @param value: the argument to this option seen on the command-line.
        
        @param parser: the MDANSEOptionParser instance.
        '''
            
        if len(parser.rargs) == 0:
            print "Registered interfaces:"
            for interfaceName in REGISTRY.get_interfaces():
                print "\t- %s" % interfaceName
        elif len(parser.rargs) == 1:
            val = parser.rargs[0]                    
            print REGISTRY.info(val.lower())
        else:
            raise CommandLineParserError("Invalid number of arguments for %r option" % opt_str)
            


    def run_job(self, option, opt_str, value, parser):
        '''Run job file(s).
            
        @param option: the option that triggered the callback.
        @type option: optparse.Option instance
        
        @param opt_str: the option string seen on the command line.
        @type opt_str: str
    
        @param value: the argument for the option.
        @type value: str
    
        @param parser: the MDANSE option parser.
        @type parser: instance of MDANSEOptionParser
        '''

        if len(parser.rargs) != 1:
            raise CommandLineParserError("Invalid number of arguments for %r option" % opt_str)

        filename = parser.rargs[0]
        
        if not os.path.exists(filename):
            raise CommandLineParserError("The job file %r could not be executed" % filename)
            
        subprocess.Popen([sys.executable, filename])


    def save_job_template(self, option, opt_str, value, parser):
        '''
        Save job templates.
            
        @param option: the option that triggered the callback.
        @type option: optparse.Option instance
        
        @param opt_str: the option string seen on the command line.
        @type opt_str: str
    
        @param value: the argument for the option.
        @type value: str
    
        @param parser: the MDANSE option parser.
        @type parser: instance of MDANSEOptionParser
        '''

        if len(parser.rargs) != 1:
            raise CommandLineParserError("Invalid number of arguments for %r option" % opt_str)
        
        jobs = REGISTRY["job"]
        
        name = parser.rargs[0]
                    
        # A name for the template is built.
        filename = os.path.abspath('template_%s.py' % name.lower())
        jobs[name].save(filename)    

        # Try to save the template for the job.  
        try:
            jobs[name].save(filename)    
        # Case where an error occured when writing the template.
        except IOError:
            raise CommandLineParserError("Could not write the job template as %r" % filename)
        # If the job class has no save method, thisis not a valid MDANSE job.
        except KeyError:
            raise CommandLineParserError("The job %r is not a valid MDANSE job" % name)
        # Otherwise, print some information about the saved template.
        else:
            print "Saved template for job %r as %r" % (name, filename)
