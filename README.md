# task_stimuli

This software is a set of cognitive tasks developed in psychopy and a system to schedule sets of tasks during a session.

Tasks are classes defined in `src/tasks`, and are instantiated in `src/sessions` files that describe a set of tasks in the session.

Material for the task (images/movies/lists...) is stored mainly in `data`

Outputs (logs, responses) are stored in the `output` folder and try to mimic a BIDS structure.

When used with option `--fmri` tasks waits for a new TTL character to start.

When used with the option `--eyetracking` this software will start Pupil, and trigger the recording of the eye movie and detected pupil position, which outputs to the `output` folder in a BIDS-like way.
Note that eyetracking data would require offline post/re-processing to be used and shared.

`utils` contains scripts to prepare movies in a reproducible way using the melt command line video editor in singularity.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## Attributions

...

## INSTALL

```
apt install python3-pip git
mkdir git
cd git

# this section is optional, only if using eyetracking
git clone https://github.com/pupil-labs/pupil.git
# follow instructions at https://docs.pupil-labs.com/#linux-dependencies

pip3 install git+https://github.com/psychopy/psychopy.git
# modify the file in psychopy that crashes
pip3 install scikit-video

git clone git@github.com:courtois-neuromod/task_stimuli.git
cd task_stimuli
mkdir output
```


## how to launch a session

`python3 main.py --subject test --session video003 --tasks videoshorttest --eyetracking --fmri -o /path/to/dataset/`

- --subject: can be whatever, will be used to save data in a bids-like structure
- --session: a session identifier that will be used to save the data in the BIDS
- --tasks: must match the name of a session script in `src/ses-<session_name>.py`, which contains the tasks to be ran on that session
- --eyetracking: turn on eyetracking, start pupil software and recording of eye
- -o : specifies the path to the root of the dataset where to output the data (in sourcedata or BIDS )

- --fmri: will wait for TTL (can be emulated with character `5` on the keyboard) to start the tasks that are labeled as fmri dependent. When not using that flag, tasks will run back to back. It will also append a video loop at the beginning of the session in order for the participant to have sound and visual stimuli to test the setup (then skip to start the session).

- --meg: TODO!


If you run multiple time this command, there are no risks of overwriting, the data will be suffixed by the date and time of start of the session.

## Creating session files

You can create new sessions by adding a `ses-xxxx.py` file in `src/sessions` folder.
Each file only create a `TASKS` list of task subclasses instances, that is loaded by the script and ran in the provided order.
Check the existing files for examples.

## Build the docker container without eyetracking and other extra hardware for task development

Build the container:

```bash
docker build --no-cache -t task_stimuli:dev .
```

Example commend to run the task with `run_docker_dev.sh`:

```bash
bash run_docker_dev.sh --subject test --session testsession --tasks mytask -o /path/to/task/output/directory`
```

The script `run_docker_dev.sh` will bind the `src` directory to the Docker image and set up other variables needed.

**`docker/` contains files for container for testing eye tracker and other shared files for docker build.**

## How to interact with the software:

### stimuli

- `5`: emulate the trigger of MRI and start task "by hand" (can be changed in `src/shared/fmri.py`)
- `<ctrl>-c` : abort and **skip** the current task and move to the next one
- `<ctrl>-n` : abort the task and restart it, showing again the instruction
- `<ctrl>-q` : quit the session, saves and close the eyetracking software

If (and only if) the software stop responding and you cannot quit, switch to the terminal and kill the software with `<ctrl>-c`.

### eyetracking

There are "hotkeys in the pupil software to trigger actions", use the buttons with these letters or type.
C (<shift>-c): launch the calibration of the eyetracking, showing markers to the participant
T (<shift>-t): a test of the calibration accuracy, also showing markers on the screen


**Important: there are two softwares running, Psychopy and Pupil, when done with calibration, click on the Stimuli window to give the focus back to Psychopy, otherwise it will not get the TTL and the task will not start with the scanner.**

This is a problem that has to be fixed in the future to avoid failed acquisition start.
Update: should be fixed now, the software takes focus when task is loaded.

# source code

psychopy scripts for stimuli presentations

src/tasks contains scripts for tasks

src/shared folder should factorize the code common across tasks

## eyetracking

The eyetracking part is managed by launching pupil capture software and launching a single recording for the whole session.

### calibration

Run a short calibration task where the subjects have to look at points shown on the screen

### gazemapping

Once the calibration has been run (though it seems that pupil reload previous calibration), pupil produces gaze information that corresponds to position on the screen.
We then display that information in almost real-time on the experimenter screen.
