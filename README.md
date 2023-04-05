# judge42

A simple judge mechanism to evaluate and autograde exams in a programming course

## Poblems statements to use in Demos:

- Demo problem statement 1: [click here](https://https://drive.google.com/file/d/1MAAfQFjSs70xd4EeNb0hSpTXa8EJReGD/view?usp=drivesdk)
- Demo problem statement 2: [click here](https://drive.google.com/file/d/1DDrM8AAZQ9W5ovhTYG8P4pdhj-UwojdN/view?usp=drivesdk)

## Demo in Google Colab: no loop, judge one problem at time

- [Cick here](https://colab.research.google.com/drive/1hrunVrsoLIi7HO6cZYb515bvsJgW4jFr?usp=sharing)

## Demo in Replit: loop

- [Click here](https://replit.com/@JuanFelipeFel49/judge42-demo?v=1)

## Usage:

```
usage: judge42.py [-h] [--dbile DBILE] [--loop | --noloop] [--nofeedback] [--norelaxed] [--python PYTHON]
                  [--source SOURCE | --stdin] [--url URL] [--version]

options:
  -h, --help       show this help message and exit
  --dbile DBILE    path to a tests database (sqlite) file, if not specified 'judge42.db' is used
  --loop           loop when --stdin was specified (default behavior)
  --noloop         don't loop when --stdin was specified
  --nofeedback     don't show differences between expected output and solution output
  --norelaxed      solution must produce exactly the expected results to full score. In relaxed option
                   (default option) scores is calculated based on similiraty ratio between solution output
                   and expected output.
  --python PYTHON  full path to python binary, default value is use python from path variable
  --source SOURCE  full path to source file as input instead of sys.stdin.
  --stdin          use stdin for input source. This is the default behavior executed in a loop (--loop
                   option).
  --url URL        download database from specified URL
  --version        show version information

```
