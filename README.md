# task_stimuli

psychopy scripts for stimuli presentations

src/tasks contains scripts for tasks

src/shared folder should factorize the code common across tasks

## eyetracking

The eyetracking part is managed by launching pupil capture software and launching a single recording for the whole session.

###calibration

Run a short calibration task where the subjects have to look at points shown on the screen

### gazemapping

Once the calibration has been run (though it seems that pupil reload previous calibration), pupil produces gaze information that corresponds to position on the screen.
We then display that information in almost real-time on the experimenter screen.


# INSTALL

```
apt install python3-pip git
mkdir git
cd git
git clone https://github.com/pupil-labs/pupil.git
# follow instructions at https://docs.pupil-labs.com/#linux-dependencies
pip3 install git+https://github.com/psychopy/psychopy.git
# modify the file in psychopy that crashes
pip3 install scikit-video

git clone git@github.com:courtois-neuromod/task_stimuli.git
cd task_stimuli
mkdir output
```
