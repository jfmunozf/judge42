# A simple judge mechanism to evaluate and autograde exams in a programming course
# Author: Juan Felipe Munoz Fernandez - jfmunozf.unal.edu.co
# Version 1.0
# Date: April 4, 2023

from os.path import exists
from os.path import getsize
from urllib import request
import sys, os
import difflib
import re
import sqlite3
import subprocess
import argparse
import signal

# Some custom Exception classes
class NoExerciseId(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message

class DBFileZeroBytes(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message

class NoIOTestsFound(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message

class NoIOTestsResultsFound(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message


class judge42:

    def __init__(self):
        self.title = "Judge42"
        self.desc = "A simple programming judge writen in Python"
        self.author = "Juan Felipe Munoz Fernandez"
        self.version = "1.0"
        self.date = "Apr 4, 2023 "
        self.email = "jfmunozf@unal.edu.co"
        self.scorepercentage = 0
        
    # Return verson information
    def getVersion(self):
        retval = "-------------------\n"
        retval += f"{self.title} - {self.version} - {self.date}" + "\n"
        retval += self.desc +"\n"
        retval += f"Author: {self.author} - {self.email}" + "\n"
        retval += "-------------------\n\n"
        return retval

    # Download database file (test cases) from URL
    # url: self explained
    # outputfilename = file name to write once file has downloaded 
    def getDBFromURL(self, url, outputfilename="judge42.db"):
        retval = False
        try:
            
            response = request.urlretrieve(url, outputfilename)
            if exists(outputfilename) and getsize(outputfilename) > 0:
                retval = True       
        except Exception as err:
            # Another error            
            raise Exception(f"ERROR in getDBFromURL(): {err}, {type(err)}")
        return retval

    # Parce source file and get exersice id
    # source: source file to search for exersice id
    def getexerciseId(self, source='source.py'):
        exerciseid = None
        pattern=[]
        try:
            with open(source) as sourcefile:
                lines = sourcefile.readlines()
                
                # Search for exercise ID in source code file.
                for line in lines:
                    pattern = re.findall("#\s*__judge42__id__\s*=\s*.*", line)
                    
                    # pattern was found break for
                    if len(pattern) > 0:
                        break

                if len(pattern) > 0:
                    pattern = pattern[0].split("=")
                    # get and exercise ID
                    exerciseid = pattern[1].strip() 
                
                # exercise ID was not found in source coude file       
                elif len(pattern) == 0:
                    # Our custm exception class            
                    raise NoExerciseId("An exercise ID was not found in source file. First line of the code must be like # __judge42__id__ = 001")
            sourcefile.close()
        
        except FileNotFoundError:
            raise Exception("ERROR: source.py file was not found")
        return exerciseid
    
    # Query database for IO tests and returns a list 
    # with all records (tests) for a particular exercise id
    # exerciseid: id of a exersice
    # dbfile: database sqlite file
    def getInputOutputTests(self, exerciseid, dbfile="judge42.db"):
        
        # A list with all records (tests) for a particular exersice id
        iotests = []

        if not exists(dbfile):
            raise FileNotFoundError(f"ERROR in getInputOutputTests(): {dbfile} file was not found")
            
        if getsize(dbfile) == 0:
            # Our custom exception class
            raise DBFileZeroBytes(f"ERROR in getInputOutputTests(): {dbfile} is 0 bytes")
        
        if exerciseid == None:
            # Our custom exception class
            raise NoExerciseId(f"ERROR in getInputOutputTests(): ID of exercise is None")
        
        try:
            conn = sqlite3.connect(dbfile)
            cur = conn.cursor()
            sql = f"SELECT * FROM tests WHERE id = '{exerciseid}'"
            cur.execute(sql)
            iotests = cur.fetchall()
            conn.close()                  
        except Exception as err:
            raise Exception(f"ERROR getInputOutputTests(): {err}, {type(err)}")
        
        if len(iotests) == 0:
                # Our custom exception class
                raise NoIOTestsFound("ERROR: I/O Tests was not found in database. Check exercise ID or a database file")
        return iotests
    
    # This method create and return a list of dictionaries.
    # Every element in list is a test (record in a database). 
    # A test is a dictionary: key is a column name of database 
    # and value is value of the field in a database.
    # iotests: tests obtained from a database. Usually
    # calling  getInputOutputTests() method
    def parseIOTests(self, iotests):
        # A list of dictionaries to return
        parsedIOTests = []      
        try:
            # Parse every test in iotests
            for test in iotests:
                # Ever test is a dictionary
                IOTest = {}
                
                # Columns in a databse for every test
                msgfail = None
                msgpass = None
                showout = False

                inputs = test[1]
                # Normalize break lines in inputs
                inputs = inputs.replace('\r\n', '\n')
                
                outputs = test[2]
                # Normalize break lines in ouputs
                outputs = outputs.replace('\r\n', '\n')

                # Obtain information from columns
                # msgfail, msgpass and showout
                if test[3] != None:
                    if len(test[3].strip()) > 0:
                        msgfail = test[3]
                if test[4] != None:
                    if len(test[4].strip()) > 0:
                        msgpass = test[4]
                if test[5] != None:
                    if test[5] == 1:
                        showout = True
                
                # A dictionary with this tests information
                IOTest['inputs'] = inputs
                IOTest['outputs'] = outputs
                IOTest['msgfail'] = msgfail
                IOTest['msgpass'] = msgpass
                IOTest['showout'] = showout
                parsedIOTests.append(IOTest)

        except Exception as err:
            raise Exception(f"ERROR in parseIOTests(): {err}, {type(err)}")
        
        if len(parsedIOTests) == 0:
            # Our custom exception class
            raise NoIOTestsFound(f"ERROR in parseIOTests(): length of parsedIOTests[] is 0")
        
        return parsedIOTests

    # Run python interpreter on source file with inputs specified in 
    # every test. Compare tun outputs with expected outpus specified 
    # for every test in a database. Return a list of dictionaries. Every
    # dictionary is a test result with detailed information to report.
    # iotests: a list of dictionaries obtained returned by calling parseIOTests()
    # python_bin: a full path to a python binary
    # sourcefile: source file to run  
    def judge(self, iotests, python_bin='python', sourcefile="source.py"):
        # Results detail for ever test
        testsresults = []
        totaltests = len(iotests)
        testcount = 1

        # Run every test in iotests
        for test in iotests:
            # This test result is a dictionary
            testresult = {}
            resultstatus = False

            # Obtain inputs and outputs specified in a test
            strinputs = test['inputs']
            stroutputs = test['outputs']
            result = None
            try:
                
                # Run Python interpreter on a source file
                result = subprocess.run([python_bin, sourcefile],
                              # Run source code with this inputs
                              input=strinputs.encode(),
                              # Get outputs from run code (source file)
                              stdout=subprocess.PIPE,
                              # Get any errors from run code (source file)
                              stderr=subprocess.PIPE,
                              # Wait until 30 seconds before kill Python run
                              timeout=30)
                
                # If any error when run source code (source file)
                if result.returncode == 1:
                    # Return code from execution (error = 1, no error = 0)
                    testresult['returncode'] = 1
                    # Test number
                    testresult['testnumber'] = testcount
                    # Status False because expected output != run output
                    testresult['status'] = False
                    # Inputs used in this tests from a database 
                    testresult['inputs'] = strinputs
                    # Expected outputs in this tests from a database
                    testresult['outputs'] = stroutputs
                    # Error message
                    testresult['msgfail'] = result.stderr.decode()
                    # No msgpass 
                    testresult['msgpass'] = None
                    # No showout
                    testresult['showout'] = False
                    # Total tests
                    testresult['numtests'] = totaltests
                    # This run output
                    testresult['output'] = result.stderr.decode()
                    # Append to the list
                    testsresults.append(testresult)
                    return testsresults
                
                # If no error in execution of source code
                elif result.returncode == 0:
                    # Get run output
                    thisresult = result.stdout.decode()
                    # Normalize break lines
                    thisresult = thisresult.replace('\r\n', '\n').strip()
                    
                    # Expeceted result for this test
                    expectedresult = stroutputs
                    # Normalize breaklines
                    expectedresult = expectedresult.replace('\r\n', '\n').strip()

                    # Compare run output with expected output for this test
                    if thisresult == expectedresult:
                        # This test OK
                        resultstatus = True

                    # No error in run code
                    testresult['returncode'] = 0
                    testresult['testnumber'] = testcount
                    # False: expected output != run output
                    # True: expected output == run output
                    testresult['status'] = resultstatus
                    # Inputs used in this tests from a database 
                    testresult['inputs'] = strinputs
                    # Expected outputs in this tests from a database
                    testresult['outputs'] = stroutputs
                    # msgfail from a database
                    testresult['msgfail'] = test['msgfail']
                    # msgpass from a database
                    testresult['msgpass'] = test['msgpass']
                    # Show or don't show expectet output for this test
                    # this is a field in a database: 1 show out, 0 or Non-value
                    # don't show expected output for this test
                    testresult['showout'] = test['showout']
                    testresult['numtests'] = totaltests
                    # output obtained from run source code on this test
                    testresult['output'] = thisresult
                    testsresults.append(testresult)
            
            # Running time exceeded
            except subprocess.TimeoutExpired:
                testresult['returncode'] = 1
                testresult['testnumber'] = testcount
                testresult['status'] = False
                testresult['inputs'] = strinputs
                testresult['outputs'] = stroutputs
                testresult['msgfail'] = "Timeout Expired: your solution exceed running time"
                testresult['msgpass'] = None
                testresult['showout'] = False
                testresult['numtests'] = totaltests
                testresult['output'] = "Timeout Expired: your solution exceed running time"
                testsresults.append(testresult)
                return testsresults
            except Exception as err:
                raise Exception(f"ERROR in writeReport(): {err}, {type(err)}")

            testcount += 1
        return testsresults

    # Return a detailed report (string) and score for every test and general score for
    # solution.
    # testresults: a results dictionary returned by calling judge() method
    # feedback: when Tru, report include differences between run output and expected output for every test
    #           when False, feedback is not provided.
    # relaxed: when True, score using similarity ratio between run output and expected output
    #          general score for a soltion is arithmetic mean of similarity ratio. When False, }
    #          general score for a solution must pass every test with 100% match betweed run 
    #          output and expected output.
    def getReport(self, testsresults, feedback=False, relaxed=False):

        if len(testsresults) == 0:
            # Our custom exception class
            raise NoIOTestsResultsFound("ERROR in getReport(): length of testsresults[] is 0")
        
        # Include version information
        report = self.getVersion()
        casereport = ""
        testcount = 1
        acumulatedratio = 0
        failedcount = 0
        passedcount = 0
        percentage = 0
        
        # Analyze every resutl in testsresults returned by judge() method
        for result in testsresults:

            # Expected outputs for this tests      
            expectedoutput = result['outputs'].splitlines()
            
            # Output for this test
            thisresult = result['output'].splitlines()
            
            diffratio = difflib.SequenceMatcher(None, result['outputs'],  result['output'])
            differences = difflib.ndiff(expectedoutput, thisresult)

            # Calculate ratio between expected outputs and run output for this test
            ratio = diffratio.ratio() * 100
            
            # If any error or expected output != run output for this test
            if result['status'] == False:
                failedcount += 1
                if not relaxed:
                    ratio = 0.0
                   
                # If any msgfail was specified for this test
                if result['msgfail'] != None:
                    report += result['msgfail'] + "\n"
                
                # If showout: show expected output for this test
                # and run output for this test
                if result['showout'] == True:
                    report += "*** Expected output ***" + "\n"
                    report += result['outputs'] + "\n"
                    report += "*** Your output ***" + "\n"
                    report += result['output'] +"\n"
                # If feedback: show differences between expected output
                # and run output
                if feedback:
                    report += "*** Differences ***" + "\n"
                    report += '\n'.join(differences) + "\n"
            
            # If expected output == run output
            elif result['status'] == True:
                passedcount += 1
                # If any msgpass was specified
                if result['msgpass'] != None:
                    report += result['msgpass'] +"\n"
            
            # This test ratio
            casereport += f"--> Case {testcount} of {result['numtests']} score: {ratio} % \n"
            report += f"--> Case {testcount} of {result['numtests']} score: {ratio} %" + "\n\n"           
            
            testcount += 1
            acumulatedratio += ratio
        
        
        if relaxed:
            # General score for solution is calculated based on mean similarity
            # ratio for every specified tests
            percentage = acumulatedratio / result['numtests']
        else:
            # General score for is a passed tests/total tests 
            percentage = passedcount / result['numtests'] * 100
        
        # Store percentage in this class field to write in result.txt later
        self.scorepercentage = percentage

        report += "---------------------------\n"
        report += casereport + "\n"
        report += f"Your solution total score: {round(percentage,3)} % " + "\n"
        report += "---------------------------\n"
        return report

    # Write report returned by getReport() in a file report.txt
    # report: strung returned by getReport()
    def writeReport(self, report):
        retval = False
        try:
            with open('report.txt',"w", encoding="utf-8") as reportfile:
                print(report, file=reportfile)
            reportfile.close()
            return True
        except Exception as err:
            raise Exception(f"ERROR in writeReport(): {err}, {type(err)}")

    # Get code from stdin and write source.py
    # user must send EOF and hit ENTER to
    # write his/her lines to source.py
    # EOF Linux: CTRL+D
    # EOF Windows: CTRL+Z
    def writeSourceFileFromStdInput(self):
        try: 
            if exists('source.py'):
                os.remove("source.py")
        except Exception as err:
            raise Exception(f"ERROR in getSourceAsInput() removing source.py: {err}, {type(err)}")
       
        try:
            lines = None
            # Multiple-line input
            lines = sys.stdin.readlines()
        except Exception as err:
            raise Exception(f"ERROR in writeSourceFileFromStdInput(): {err}, {type(err)}")
        

        try:
            # Write lines from stdin in a file source.py when user sends EOF sequence
            with open('source.py', mode="w", encoding="utf-8") as sourcefile:
                sourcefile.writelines(lines)
            sourcefile.close()
        except Exception as err:
            raise Exception(f"ERROR in getSourceAsInput() opening source.py: {err}, {type(err)}")

    # Write report.txt for auto grading purposes 
    # this file store only a percentage of solution
    # after judging it   
    def writeScorePercentage(self):
        with open('result.txt', mode="w", encoding="utf-8") as resultfile:
            print(self.scorepercentage, file=resultfile)
        resultfile.close()
    
    def getInstructions(self):
        retval = "\n    INSTRUCTIONS\n\n"
        eofkey = "CTRL+D"
        if sys.platform.startswith("win32"):            
            eofkey = "CTRL+Z"
        retval += "--> Copy and paste your code below: right click and paste\n"
        retval += "--> first line of code must include id of your exercise\n"
        retval += "--> hit [ENTER] + " + eofkey + " to check your code\n"
        retval += "--> press CTRL+C to terminate this program\n\n"        
        
        return retval

    # To capture CTRL+C signal to diplomatic exit
    def ctrlCHandler(self, signum, frame):
        print("\n--> CTRL+C was pressed")
        print("--> Bye!")
        sys.exit(0)

if __name__ == '__main__':
    
    if sys.version_info[0] < 3:
        print("This script requires Python version 3 or newer")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    group1 = parser.add_mutually_exclusive_group()
    group2 = parser.add_mutually_exclusive_group()    
    parser.add_argument("--dbfile", help="path to a tests database (sqlite) file, if file not specified 'judge42.db' is used", default="judge42.db", required=False) 
    group2.add_argument("--loop", help="loop when --stdin was specified (default behavior)", action="store_true", default=True, required=False)
    group2.add_argument("--noloop", help="don't loop when --stdin was specified", action="store_true", default=False, required=False)
    parser.add_argument("--feedback", help="show differences between expected output and solution output. Default behavior does not show differences between expected output and solution output", action="store_true", default=False, required=False) 
    parser.add_argument("--relaxed", help="solution must produce exactly the expected results to full score, this is default behavior. In relaxed option, scores are calculated based on similarity ratio between solution output and expected output.", action="store_true", default=False, required=False)
    parser.add_argument("--python", help="full path to python binary, default value is use python from path variable", default='python', required=False)
    group1.add_argument("--source", help="full path to source file as input instead of sys.stdin. Option --noloop is atomatically used when source file is specified", required=False)
    group1.add_argument("--stdin", help="use stdin for input source code. This is the default behavior executed in a loop (--loop option).", default=True, required=False, action="store_true")
    parser.add_argument("--url", help="download tests database from specified URL", required=False)
    parser.add_argument("--version", help="show version information", action="store_true", default=False, required=False)    
    args = parser.parse_args()
    
    j42 = judge42()
    
    # To capture CTRL+C signal
    signal.signal(signal.SIGINT, j42.ctrlCHandler)
    
    if args.version:
        print(j42.getVersion())
        sys.exit(0)
    
    if args.url:
        print(f"Download database from URL: {args.url} ...")
        if (j42.getDBFromURL(args.url)):
            print(f"Download database from URL: {args.url} ... OK")
        else:
            print(f"Download database from URL: {args.url} ... FAILED")              
    
    if args.source != None:
        try:
            exerciseid = j42.getexerciseId(args.source) 
            iotests = j42.getInputOutputTests(exerciseid, dbfile=args.dbfile)
            iotests = j42.parseIOTests(iotests)
            testsresults = j42.judge(iotests, python_bin=args.python, sourcefile=args.source)
            report = j42.getReport(testsresults, feedback=args.feedback, relaxed=args.relaxed)
            j42.writeReport(report)
            j42.writeScorePercentage()
            print(report)
            sys.exit(0)
        except Exception as err:
            print(f"ERROR: {err}, {type(err)}") 
                
    elif args.stdin and args.noloop:
        try:
            print(j42.getInstructions())
            j42.writeSourceFileFromStdInput()
            exerciseid = j42.getexerciseId()   
            iotests = j42.getInputOutputTests(exerciseid, dbfile=args.dbfile)
            iotests = j42.parseIOTests(iotests)
            testsresults = j42.judge(iotests, python_bin=args.python, sourcefile='source.py')
            report = j42.getReport(testsresults, feedback=args.feedback, relaxed=args.relaxed)
            j42.writeReport(report)
            j42.writeScorePercentage()
            print(report)            
            sys.exit(0)
        except Exception as err:
            print(f"ERROR: {err}, {type(err)}") 

    elif args.stdin and args.loop:
        while True:
            print(j42.getInstructions())
            j42.writeSourceFileFromStdInput()
            try:
                exerciseid = j42.getexerciseId()   
                iotests = j42.getInputOutputTests(exerciseid, dbfile=args.dbfile)
                iotests = j42.parseIOTests(iotests)
                testsresults = j42.judge(iotests, python_bin=args.python, sourcefile='source.py')
                report = j42.getReport(testsresults, feedback=args.feedback, relaxed=args.relaxed)
                j42.writeReport(report)
                j42.writeScorePercentage()
                print(report)
                input("--> Press [ENTER] to continue <--")
            except Exception as err:
                print(f"ERROR: {err}, {type(err)}")            
        sys.exit(0)
    

