import os, sys, time, itertools, random, copy
from colorama import Fore
from psychopy import visual, core, data, logging, event
from pyglet.window import key
from .task_base import Task

from ..shared import config, utils

STIMULI_DURATION = 4
BASELINE_BEGIN = 5
BASELINE_END = 5
ISI = 1
IMAGES_FOLDER = "/home/basile/data/projects/task_stimuli/BOLD5000_Stimuli/Scene_Stimuli/Presented_Stimuli/ImageNet"

STIMULI_SIZE = (400, 400)

quadrant_id_to_pos = [(-200, 100), (200, 100), (-200, -100), (200, -100)]


class ImagePosition(Task):

    DEFAULT_INSTRUCTION = """You will be presented a set of items in different quadrant of the screen.
Try to remember the items and their location on the screen."""

    def __init__(self, items_list, *args, **kwargs):
        super().__init__(**kwargs)
        # TODO: image lists as params, subjects ....
        self.item_list = data.importConditions(items_list)

    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield ()

    def _run(self, exp_win, ctl_win):

        trials = data.TrialHandler(self.item_list, 1, method="sequential")
        img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="pix")
        exp_win.logOnFlip(
            level=logging.EXP, msg="memory: task starting at %f" % time.time()
        )
        for frameN in range(config.FRAME_RATE * BASELINE_BEGIN):
            yield ()
        for trial in trials:
            image_path = trial["image_path"]
            img.image = image_path
            img.pos = quadrant_id_to_pos[trial["quadrant"]]
            exp_win.logOnFlip(
                level=logging.EXP,
                msg="memory: display %s in quadrant %d"
                % (image_path, trial["quadrant"]),
            )
            for frameN in range(config.FRAME_RATE * STIMULI_DURATION):
                img.draw(exp_win)
                if ctl_win:
                    img.draw(ctl_win)
                yield ()
            exp_win.logOnFlip(level=logging.EXP, msg="memory: rest")
            for frameN in range(config.FRAME_RATE * ISI):
                yield ()
        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield ()


class NumberPair(Task):

    DEFAULT_INSTRUCTION = """You will be presented a 6 x 4 grid on the screen.
Try to remember the numer pairs on screen.
You will be asked to recall them seqentially."""

    def __init__(self, items_list, *args, **kwargs):
        super().__init__(**kwargs)
        self.item_list = data.importConditions(items_list)
        self.duration = len(self.item_list)
        self._progress_bar_refresh_rate = 2
        self.trials = data.TrialHandler(self.item_list, 1, method="sequential")
        self.grid_size = (6, 4)
        self.direction_keys = {'left': -1, 'right': 1, 'up': -1, 'down': 1}
        self.confidence_keys = {'a': 'yes', 's': 'no'}

    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        for _ in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield True

    def _setup(self, exp_win):
        # make pares of rectangels and text stim
        self.grid = [(
            visual.TextStim(
                exp_win, text="", pos=(-0.8 + x * 0.25, 0.7 - y * 0.25),
                alignText="center", color="white"
            ),
            visual.Rect(
                exp_win, size=(0.2, 0.2), pos=(-0.8 + x * 0.25, 0.7 - y * 0.25),
                fillColor=None,
            )
            )
            for y, x in itertools.product(range(self.grid_size[1]), range(self.grid_size[0]))
        ]  # fill the grid from top left corner, left to right first
        recall_instruction = (f"Use the arrow keys to move the selected box."
                              "\nI am sure: press "
                              f"\"{list(self.confidence_keys.keys())[0]}\" "
                              "to move on.\nI am not sure: press "
                              f"\"{list(self.confidence_keys.keys())[1]}\""
                              " to move on.")
        self.answer_instruction = visual.TextStim(
            exp_win, text=recall_instruction,
            pos=(-0.8 + 2 * 0.25, 0.7 - 5 * 0.25),
            alignText="left", color="white"
        )
        self.question = visual.TextStim(
            exp_win, text="",
            pos=(0, 0.5),
            alignText="center", color="white")

        self.recall_time = visual.RatingScale(
            exp_win, low=15, high=75, precision=1,
            tickMarks=[15, 75],
            labels=["15 seconds", "75 seconds"], scale=None, noMouse=True
        )
        self.recall_time.styleTweaks = ['triangleMarker']
        self._progress_bar_refresh_rate = 2 # 1 flip / trial
        self.pyglet_keyboard = key.KeyStateHandler()

    def _run(self, exp_win, ctl_win):
        # start the trials
        last_selected_location = None
        for trial in self.trials:
            # flush keys
            confidence_answer_keys = event.getKeys(keyList=list(self.confidence_keys.keys()))
            change_direction = event.getKeys(keyList=list(self.direction_keys.keys()))

            # update the display
            items = trial["display"]
            for item, cell in zip(items, self.grid):
                cell[0].text = item

            if last_selected_location:
                self.grid[last_selected_location][-1].lineColor = 'white'

            if trial['trial_type'] == 'recall':
                # set a random box that's not the box with number in as the start
                selected_location = self._selecte_start_location(trial['recall_display'])
                self.trials.addData("random_start_location", selected_location)
                self.grid[selected_location][-1].lineColor = 'yellow'

            if trial['trial_type'] in ["estimate", "performance"]:
                # update text
                self.question.text = trial['display']
                pos = 50
                self.recall_time.markerStart = pos
                exp_win.winHandle.push_handlers(self.pyglet_keyboard)


            # display progress
            description = f"Trial {trial['trial_number']}: {trial['trial_type']}"
            if trial['trial_type'] == 'recall':
                loc_x, loc_y = self._index2coordinates(selected_location)
                description = f"Trial {trial['trial_number']}: {trial['trial_type']}-{trial['pair_number']} selecting {selected_location}({loc_x}, {loc_y})"
            self.progress_bar.set_description(description)

            trial["onset_flip"] = self._exp_win_last_flip_time - self._exp_win_first_flip_time

            for frameN in range(int(config.FRAME_RATE * trial["duration"]) - 1):  # use the time of one frame to prepare
                if trial['trial_type'] in ['rehersal', 'fixation', 'recall']:  # rehersal or fixation
                    for item, box in self.grid:
                        item.draw(exp_win)
                        box.draw(exp_win)
                        if ctl_win:
                            item.draw(exp_win)
                            box.draw(exp_win)
                    if trial['trial_type'] == 'recall':
                        for item, box in self.grid:
                            item.draw(exp_win)
                            box.draw(exp_win)
                            if ctl_win:
                                item.draw(exp_win)
                                box.draw(exp_win)
                        # show instruction
                        self.answer_instruction.draw(exp_win)
                        if ctl_win:
                            self.answer_instruction.draw(exp_win)

                        # detect key press for location, update color of selected block
                        last_selected_location = selected_location
                        change_direction = event.getKeys(keyList=list(self.direction_keys.keys()))
                        if len(change_direction):
                            selected_location = self._find_next_location(change_direction, selected_location, trial['recall_display'])
                            # update screen buffer
                            self.grid[selected_location][-1].lineColor = 'yellow'
                            if selected_location != last_selected_location:
                                self.grid[last_selected_location][-1].lineColor = 'white'
                            # update progress bar
                            loc_x, loc_y = self._index2coordinates(selected_location)
                            description = f"Trial {trial['trial_number']}: {trial['trial_type']}-{trial['pair_number']} selecting {selected_location}({loc_x}, {loc_y})"
                            self.progress_bar.set_description(description)

                        # detect key press for metacognition answer
                        confidence_answer_keys = event.getKeys(keyList=list(self.confidence_keys.keys()), timeStamped=self.task_timer)
                        if len(confidence_answer_keys):
                            first_response = confidence_answer_keys[0]
                            self.trials.addData("selected_location", selected_location)
                            self.trials.addData("confidence_key", first_response[0])
                            self.trials.addData("confidence_key_onset", first_response[1])
                            self.trials.addData("confidence_rating", self.confidence_keys[first_response[0]])
                            self.trials.addData("correct", int(trial['recall_answer'] == selected_location))
                            self.trials.addData("recall_time", first_response[1] - trial["onset_flip"])
                            description = f"{Fore.RED}Trial {trial['trial_number']}: {trial['trial_type']}-{trial['pair_number']} selecting {selected_location}({loc_x}, {loc_y}), confident? {self.confidence_keys[first_response[0]]} keypress: {first_response[0]}{Fore.RESET}"
                            self.progress_bar.set_description(description)
                            # reset color
                            last_selected_location = selected_location
                            break  # temporay solution
                elif trial['trial_type'] in ["estimate"]:
                    self.question.draw(exp_win)
                    self.recall_time.draw()
                    if ctl_win:
                        self.question.draw(exp_win)
                        self.recall_time.draw()

                    if self.pyglet_keyboard[key.LEFT]:
                        pos -= 1.0
                    elif self.pyglet_keyboard[key.RIGHT]:
                        pos += 1.0
                    if pos > 75:
                        pos = 75
                    elif pos < 15:
                        pos = 15
                    self.recall_time.setMarkerPos(pos)
                else:
                    pass
                yield True
            yield True

    def _find_next_location(self, change_direction, selected_location, recall_display):
        loc_x, loc_y = self._index2coordinates(selected_location)
        # check what's the max some one has moved in each direction
        for direction in change_direction:
            if direction in ['left', 'right']:
                loc_x += self.direction_keys[direction]
                # chek if it's the edge
                loc_x = self._check_edge(loc_x, "x")
            else:
                loc_y += self.direction_keys[direction]
                # chek if it's the edge
                loc_y = self._check_edge(loc_y, "y")
        selected_location = self._coordinates2index(loc_x, loc_y)
        if selected_location != int(recall_display):
            return selected_location

        # if the selected grid is on the display and on the edge, don't move
        # if the selection is on the display and in the middle, skip the cell
        if direction in ['left', 'right']:
            if loc_x in [0, self.grid_size[0] - 1]:  # on the edge
                loc_x -= self.direction_keys[direction]  # don't move
            else:
                loc_x += self.direction_keys[direction]  # move past the cell
        elif loc_y in [0, self.grid_size[-1] - 1]:  # on the edge
            loc_y -= self.direction_keys[direction] # don't move
        else:
            loc_y += self.direction_keys[direction] # move past the cell
        return self._coordinates2index(loc_x, loc_y)

    def _check_edge(self, loc, dir):
        dir2idx = {"x":0, "y": -1}
        if loc < 0:
            return 0
        elif loc >= (self.grid_size[dir2idx[dir]]):
            return self.grid_size[dir2idx[dir]] - 1
        return loc

    def _index2coordinates(self, selected_location):
        loc_x = selected_location % self.grid_size[0]
        loc_y = selected_location // self.grid_size[0]
        return loc_x, loc_y

    def _coordinates2index(self, loc_x, loc_y):
        return loc_x + (loc_y * self.grid_size[0])

    def _selecte_start_location(self, recall_display):
        selected_location = list(range(self.grid_size[0] * self.grid_size[1]))
        selected_location = selected_location[:int(recall_display)] + \
            selected_location[int(recall_display) + 1:]
        random.shuffle(selected_location)
        return selected_location[0]

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False
