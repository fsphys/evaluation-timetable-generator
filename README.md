## Timetable Generator for Lecture Evaluation

Python script to generate a timetable from a long list of lectures.
Used to organise the evaluation of lectures at KIT's physics department.
The script reads a list of lecture IDs form a CSV file and queries [KitHub](http://www.kithub.de/)'s API to retrieve
information about them.
As output, an OpenDocument Spreadsheet file is generated.


## Prerequisites

* Python 3
* [simpleodspy](https://pypi.python.org/pypi/simpleodspy). As the current version has a bug that makes it impossible to insert text in cells, use the [fork of blipp](), where this is fixed:
    * `pip install git+https://github.com/blipp/simpleodspy.git@fix-decoding-str`
* [odfpy](https://pypi.python.org/pypi/odfpy), the most recent version supports Python 3 and is available on GitHub: https://github.com/eea/odfpy . Follow the instructions in the readme there to install it.


## Usage

At the end of this section, a recommended workflow for using this script is described.


### Get the code

Clone this repository or simply download the file `evaluation.py`.


### Configuration

Configuration is currently done at the beginning of the Python file `evaluation.py`.
To set up the script for a new semester, `term_id` has to be adapted.
This is the ID of the semester within KitHub's database.
The right number can be retrieved from [](http://www.kithub.de/api/#!/terms/GET-terms---format-_get_0), just click “Try it out!”.
The time interval for which the timetable will be generated has to be specified with `eva_starttime_str` and `eva_endtime_str`.


### Input data

By default, the script expects a file `input.csv` in its working directory.
This file has to follow a certain format:
* The column delimiter needs to be `,` and `"` needs to be used for quoting strings.
* The first row is the header and will be ignored.
* 1st column: the lecture ID's used in KIT's official university calendar, called “Lehrveranstaltungsnummer”. This ID will be used to query KitHub's API.
* 2nd column: short string describing the course of studies, as we have at least three different ones at our department. This will be printed in the timetable.
* 3rd column: name of the lecture, as it should be printed in the timetable. Some lectures have very long official titles, but very common abbreviations.
* 4th column: if an `x` is entered here, the lecture will be ignored.
* 5th column: if an `x` is entered here, a note will be added to the end of the name of the lecture to indicate that an exercise course belonging to the lecture has to be evaluated as well.
* 6th column: if an `x` is entered here, a note will be added to the end of the name of the lecture to indicate that a laboratory course belonging to the lecture has to be evaluated as well.

There is no special reason why the input file has to be CSV, other than that simpleodspy currently has problems reading OpenDocument Spreadsheet documents.


### Run the script

Execute `./evaluation.py` in the directory where the script is located.


### Output

The downloaded lecture data will be written to JSON files in a subdirectory `courses`.
By default, the script writes the timetable to `timetable.ods` and a file `output.ods` in the current working directory.
The file `output.ods` is a copy of `input.csv` with two additional columns.
These can be used to check certain functions of the script:
* 7th column: an indicator if an appointment was found within the specified time frame. The cell will be coloured red, if none was found, and yellow, if the lecture was ignored due to an `x` in th 4th column.
* 8th column: contains the name of the lecture as it was returned by KitHub's API. If the name in the 3rd column differs from it, the cell will be coloured red. This can be used to check if the lecture ID and the lecture name don't match.


### Workflow

1. Prepare an OpenDocument Spreadsheet document, for example called `input.ods`, that fulfills the requirements described above.
2. Export it as CSV to `input.csv`.
3. Call the script.
4. Open `output.ods` to check what has been done. Decide which lectures to mark as ignored, and which ones to include an exercise or laboratory course. Note: of course some in this case actually not too difficult pattern matching logic could be used to determine which lectures belong together, but for the first version of the script, this has not yet been done.
5. Go to step 2 if you changed anything. If not, check if `timetable.ods` fits your needs and go to step 4 if you need change the input file again.
6. Adjust the formatting of `timetable.ods` if needed.


## Acknowledgements

Thanks to [Carsten Griesheimer](http://www.carstengriesheimer.de/), the creator of [KitHub](http://www.kithub.de/), for providing an API to the data and for adapting the API for our needs.
