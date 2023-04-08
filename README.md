# judge42

A simple judge mechanism to evaluate and autograde exams in a programming course

## Poblems statements to use in demos:

- Demo problem statement 1: [click here](https://https://drive.google.com/file/d/1MAAfQFjSs70xd4EeNb0hSpTXa8EJReGD/view?usp=drivesdk)
- Demo problem statement 2: [click here](https://drive.google.com/file/d/1DDrM8AAZQ9W5ovhTYG8P4pdhj-UwojdN/view?usp=drivesdk)

## Demo in Google Colab: no loop, judge one problem at time

- [Cick here](https://colab.research.google.com/drive/1hrunVrsoLIi7HO6cZYb515bvsJgW4jFr?usp=sharing)

## Demo in Replit: looping in a console application

- [Click here](https://replit.com/@JuanFelipeFel49/judge42-demo?v=1)

## Demo in Replit: using a simple web app with Flask:

- [Click here](https://replit.com/@JuanFelipeFel49/judge42-flask?v=1)

## Usage in command line:

```
usage: judge42.py [-h] [--dbfile DBFILE] [--loop | --noloop] [--feedback]
                  [--relaxed] [--python PYTHON] [--source SOURCE | --stdin]
                  [--url URL] [--version]

options:
  -h, --help       show this help message and exit
  --dbfile DBFILE  path to a tests database (sqlite) file, if file not
                   specified 'judge42.db' is used
  --loop           loop when --stdin was specified (default behavior)
  --noloop         don't loop when --stdin was specified
  --feedback       show differences between expected output and solution
                   output. Default behavior does not show differences between
                   expected output and solution output
  --relaxed        solution must produce exactly the expected results to full
                   score, this is default behavior. In relaxed option, scores
                   are calculated based on similarity ratio between solution
                   output and expected output.
  --python PYTHON  full path to python binary, default value is use python
                   from path variable
  --source SOURCE  full path to source file as input instead of sys.stdin.
                   Option --noloop is atomatically used when source file is
                   specified
  --stdin          use stdin for input source code. This is the default
                   behavior executed in a loop (--loop option).
  --url URL        download tests database from specified URL
  --version        show version information

```
