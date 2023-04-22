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

DIRECTIONS = {
    "left": -1,
    "right": 1,
    "up": -1,
    "down": 1
}

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

    DEFAULT_INSTRUCTION = """You will be presented a 6 x 4 grid mixed with numbers and alphabets on the screen.
Remember the locations of the numer pairs on screen.
You will be asked to recall them seqentially, and win one point per correct pair.
If you can remeber all the pair, you will win the bonus points.
"""

    def __init__(self, items_list, total_possible_points, *args, **kwargs):
        super().__init__(**kwargs)
        self.total_possible_points = total_possible_points
        self.item_list = data.importConditions(items_list)
        self.duration = len(self.item_list)  # not sure if this is needed
        self._progress_bar_refresh_rate = 2
        self.trials = data.TrialHandler(self.item_list, 1, method="sequential")
        self.grid_size = (6, 4)
        # self.direction_keys = {"left": "a", "right": "d", "up": "w", "down": "s"}  # laptop
        # self.direction_values = {"a": DIRECTIONS["left"],
        #                         "d": DIRECTIONS["right"],
        #                         "w": DIRECTIONS["up"],
        #                         "s": DIRECTIONS["down"]}  # laptop
        # self.confidence_keys = {'yes': 'k', 'no': 'l'}  # laptop
        # self.rating_pygame = {"left": key.A, "right": key.D}  # laptop
        self.confidence_keys = {'yes': 'a', 'no': 'b'}  # mri
        self.direction_keys = {"left": "l", "right": "r", "up": "u", "down": "d"}   # mri
        self.direction_values = {"l": DIRECTIONS["left"],
                                 "r": DIRECTIONS["right"],
                                 "u": DIRECTIONS["up"],
                                 "d": DIRECTIONS["down"]}  # mri
        self.rating_pygame = {"left": key.L, "right": key.R}  # mri

    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )
        instruction_duration = 10
        for _ in range(config.FRAME_RATE * instruction_duration):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield True

        message = (
            f"In this session, "
            f"you can earn up to {self.total_possible_points} pionts.")
        duration = 3
        screen_text.text = message
        for _ in range(config.FRAME_RATE * duration):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(exp_win)
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
                              f"\"{self.confidence_keys['yes']}\" "
                              "to move on.\nI am not sure: press "
                              f"\"{self.confidence_keys['no']}\""
                              " to move on.")
        self.answer_instruction = visual.TextStim(
            exp_win, text=recall_instruction,
            pos=(-0.8 + 2 * 0.25, 0.7 - 5 * 0.25),
            alignText="left", color="white"
        )
        self.postanswer_message = visual.TextStim(
            exp_win, text="Response received. Wait for the next trial.",
            pos=(-0.8 + 2 * 0.25, 0.7 - 5 * 0.25),
            alignText="left", color="white"
        )
        self.question = visual.TextStim(
            exp_win, text="",
            # pos=(0, 0.5),
            alignText="center", color="white",
            wrapWidth=config.WRAP_WIDTH)

        self.recall_time = visual.RatingScale(
            exp_win, low=5, high=60, precision=1,
            tickMarks=[5, 60],
            labels=["5 seconds", "60 seconds"], scale=None, noMouse=True,
            leftKeys=self.direction_keys['left'],
            rightKeys=self.direction_keys['right'],
            acceptKeys=self.confidence_keys['yes'],
            maxTime=0,
        )
        self.recall_time.styleTweaks = ['triangleMarker']
        self.recall_time.keyClick = "Press left or right"

        self.effort = visual.RatingScale(
            exp_win, low=0, high=100, precision=1,
            tickMarks=[0, 100],
            labels=["0%", "100%"], scale=None, noMouse=True,
            leftKeys=self.direction_keys['left'],
            rightKeys=self.direction_keys['right'],
            acceptKeys=self.confidence_keys['yes'],
            maxTime=0,
        )
        self.effort.styleTweaks = ['triangleMarker']
        self.effort.keyClick = "Press left or right"

        self._progress_bar_refresh_rate = 2 # 1 flip / trial
        self.pyglet_keyboard = key.KeyStateHandler()

    def _run(self, exp_win, ctl_win):
        # start the trials
        total_earned_points = 0

        for trial in self.trials:
            # flush keys
            last_selected_location = None
            confidence_answer_keys = event.getKeys(
                        keyList=list(self.confidence_keys.values()),
                        timeStamped=self.task_timer)
            change_direction = event.getKeys(keyList=list(self.direction_keys.values()))
            exp_win.winHandle.push_handlers(self.pyglet_keyboard)
            # display progress
            description = f"Trial {trial['i_grid']}: {trial['event_type']}. {trial['duration']}s"
            self.progress_bar.set_description(description)
            # trial onset
            trial["onset"] = self._exp_win_last_flip_time - self._exp_win_first_flip_time

            # subject estimate time for encoding part
            if trial['event_type'] in ["estimate"]:
                n_correct = 0  # reset correct counter
                self.recall_time.reset()
                self.question.text = (
                    f"{trial['target_score']} of number pairs to remember.\n"
                    f"{trial['reward_level']} bonus points to win if you get"
                    " all pairs correct."
                )
                pos = random.randrange(5, 60)
                self.recall_time.markerStart = pos
                grid_memory_time = None
                while self.recall_time.noResponse:
                    # use a sliding scale to select time one wants to use for
                    # memorising the grid
                    self.question.draw(exp_win)
                    self.recall_time.draw(exp_win)
                    if ctl_win:
                        self.question.draw(exp_win)
                        self.recall_time.draw(exp_win)

                    pos = self._update_rating_scale(pos, 0, 55)
                    self.recall_time.setMarkerPos(pos)
                    yield True
                grid_memory_time = self.recall_time.getRating()
                self.trials.addData('estimate_time',
                                    grid_memory_time)
                self.trials.addData('decision_time',
                                    self.recall_time.getRT())
                self.trials.addData('choice_history',
                                    self.recall_time.getHistory())
                description = (f"{Fore.RED}Trial {trial['i_grid']}: "
                               f"{trial['event_type']}-{trial['pair_number']} "
                               f"selecting {grid_memory_time}{Fore.RESET}")
                yield True

            elif trial['event_type'] in ['encoding', 'recall']:
                # reset grid display
                for item, cell in zip(trial["grid"], self.grid):
                    cell[0].text = item
                    cell[-1].lineColor = 'white'  # reset grid color

                if trial['event_type'] == 'encoding':
                    trial["duration"] = int(grid_memory_time) \
                        if grid_memory_time else 5  # in case no response received
                    description = f"Trial {trial['i_grid']}: {trial['event_type']}. {trial['duration']}s"
                    self.progress_bar.set_description(description)
                    deadline = trial["onset"] + trial["duration"] - 1 / config.FRAME_RATE
                    for item, box in self.grid:
                        item.draw(exp_win)
                        box.draw(exp_win)
                        if ctl_win:
                            item.draw(exp_win)
                            box.draw(exp_win)
                    yield True
                    utils.wait_until(self.task_timer, deadline)

                elif trial['event_type'] == 'recall':
                    # set a random box that's not the box with number in as the start
                    selected_location = self._selecte_start_location(trial['recall_display'])
                    self.trials.addData("random_start_location", selected_location)
                    self.grid[selected_location][-1].lineColor = 'yellow'
                    loc_x, loc_y = self._index2coordinates(selected_location)
                    description = (f"Trial {trial['i_grid']}: "
                                f"{trial['event_type']}-{trial['pair_number']} "
                                f"selecting {selected_location}({loc_x}, {loc_y})")
                    self.progress_bar.set_description(description)
                    collect_response = False
                    selection_history = [(selected_location, 0)]
                    while collect_response is False:
                        for item, box in self.grid:
                            item.draw(exp_win)
                            box.draw(exp_win)
                            if ctl_win:
                                item.draw(exp_win)
                                box.draw(exp_win)
                        # collect response
                        self.answer_instruction.draw(exp_win)
                        if ctl_win:
                            self.answer_instruction.draw(exp_win)
                        yield True
                        # detect key press for location, update color of selected block
                        last_selected_location = selected_location
                        change_direction = event.getKeys(keyList=list(self.direction_keys.values()))
                        if len(change_direction):
                            change_direction_timestamp = self.task_timer.getTime() - trial['onset']
                            selected_location = self._find_next_location(
                                change_direction, selected_location,
                                trial['recall_display'])
                            selection_history.append((selected_location, change_direction_timestamp))
                            # update screen buffer
                            self.grid[selected_location][-1].lineColor = 'yellow'
                            if selected_location != last_selected_location:
                                self.grid[last_selected_location][-1].lineColor = 'white'

                            # update progress bar
                            loc_x, loc_y = self._index2coordinates(selected_location)
                            description = (
                                f"Trial {trial['i_grid']}: "
                                f"{trial['event_type']}-{trial['pair_number']} "
                                f"selecting {selected_location}({loc_x}, {loc_y})"
                            )
                            self.progress_bar.set_description(description)
                            for item, box in self.grid:
                                item.draw(exp_win)
                                box.draw(exp_win)
                                if ctl_win:
                                    item.draw(exp_win)
                                    box.draw(exp_win)
                            # collect response
                            self.answer_instruction.draw(exp_win)
                            if ctl_win:
                                self.answer_instruction.draw(exp_win)
                            yield True

                        confidence_answer_keys = event.getKeys(
                            keyList=list(self.confidence_keys.values()),
                            timeStamped=self.task_timer)
                        if len(confidence_answer_keys):
                            collect_response = True
                    # detect key press for metacognition answer
                    first_response = confidence_answer_keys[0]
                    recall_correct = int(int(trial['recall_answer']) == int(selected_location))
                    confidence_rating = [k for k, v in self.confidence_keys.items() if v == first_response[0]][0]
                    n_correct += recall_correct
                    self.trials.addData("selected_location", selected_location)
                    self.trials.addData("confidence_key", first_response[0])
                    self.trials.addData("confidence_key_onset", first_response[1])
                    self.trials.addData("confidence_rating", confidence_rating)
                    self.trials.addData("correct", recall_correct)
                    self.trials.addData("choice_history", selection_history)
                    self.trials.addData("decision_time", first_response[1] - trial["onset"])
                    description = (f"{Fore.RED}Trial {trial['i_grid']}: "
                                    f"{trial['event_type']}-{trial['pair_number']} "
                                    f"selecting {selected_location}({loc_x}, {loc_y}), "
                                    f"confident? {confidence_rating} "
                                    f"correct? {recall_correct} "
                                    f"keypress: {first_response[0]}{Fore.RESET}")
                    self.progress_bar.set_description(description)
                    # reset color
                    last_selected_location = selected_location

            elif trial['event_type'] == "e_success":
                # update text
                self.estimate_success = visual.RatingScale(
                    exp_win,
                    choices=list(range(int(trial['target_score']) + 1)),
                    noMouse=True, precision=1,
                    leftKeys=self.direction_keys['left'],
                    rightKeys=self.direction_keys['right'],
                    acceptKeys=self.confidence_keys['yes'],
                    maxTime=0,
                )
                self.estimate_success.keyClick = "Press left or right"
                self.estimate_success.styleTweaks = ['triangleMarker']
                self.question.text = f"Out of {trial['target_score']} number pairs, how many did you get right?"
                pos = int(trial['target_score'])
                self.estimate_success.markerStart = pos

                while self.estimate_success.noResponse:
                    self.question.draw(exp_win)
                    self.estimate_success.draw(exp_win)
                    if ctl_win:
                        self.question.draw(exp_win)
                        self.estimate_success.draw(exp_win)
                    yield True
                estimate_success = self.estimate_success.getRating()
                self.trials.addData('estimate_success', estimate_success)
                self.trials.addData('decision_time', self.estimate_success.getRT())
                self.trials.addData('choice_history', self.estimate_success.getHistory())
                description = f"{Fore.RED}Trial {trial['i_grid']}: {trial['event_type']} selecting {estimate_success}{Fore.RESET}"
                self.progress_bar.set_description(description)
                yield True

            elif trial['event_type'] == "feedback":
                # update text
                bonus_point = 0 if n_correct != int(trial["target_score"]) else int(trial["reward_level"])
                self.trials.addData('bonus_point', bonus_point)
                total_earned_points += bonus_point + n_correct
                message = (
                    f"Out of {trial['target_score']} number pairs, "
                    f"you got {n_correct} correctly.\n"
                    f"You got {bonus_point} bonus pionts. "
                    f"You received {n_correct + bonus_point} points from "
                    "this trial.")
                n_frame = int(config.FRAME_RATE * trial["duration"]) - 1
                self.question.text = message
                for _ in range(n_frame):
                    self.question.draw(exp_win)
                    if ctl_win:
                        self.question.draw(exp_win)
                    yield True

            elif trial['event_type'] in ["effort"]:
                # update text
                self.effort.reset()
                self.question.text = f"How much effor did you put in the task?"
                pos = random.randrange(0, 100)
                self.effort.markerStart = pos
                effort_estmation = None
                while self.effort.noResponse:
                    # use a sliding scale to select time one wants to use for
                    # memorising the grid
                    self.question.draw(exp_win)
                    self.effort.draw(exp_win)
                    if ctl_win:
                        self.question.draw(exp_win)
                        self.effort.draw(exp_win)

                    pos = self._update_rating_scale(pos, 0, 100)
                    self.effort.setMarkerPos(pos)
                    yield True
                effort_estmation = self.effort.getRating()
                self.trials.addData('effort',
                                    effort_estmation)
                self.trials.addData('decision_time',
                                    self.effort.getRT())
                self.trials.addData('choice_history',
                                    self.effort.getHistory())
                description = (f"{Fore.RED}Trial {trial['i_grid']}: "
                               f"{trial['event_type']} "
                               f"selecting {effort_estmation}{Fore.RESET}")
                self.progress_bar.set_description(description)
                yield True

            elif trial['event_type'] == "isi":
                utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] - 1 / config.FRAME_RATE)
                yield True
            else:
                pass
            self.progress_bar.set_description(description)
            yield True

        # final results screen
        message = (
            f"In this session, "
            f"you earned {total_earned_points} out of "
            f"{self.total_possible_points} pionts.")
        duration = 3
        n_frame = int(config.FRAME_RATE * duration) - 1
        self.question.text = message
        for _ in range(n_frame):
            self.question.draw(exp_win)
            if ctl_win:
                self.question.draw(exp_win)
            yield True

    def _update_rating_scale(self, pos, min, max):
        if self.pyglet_keyboard[self.rating_pygame['left']]:
            pos -= 1.0
        elif self.pyglet_keyboard[self.rating_pygame['right']]:
            pos += 1.0

        if pos > max:
            pos = max
        elif pos < min:
            pos = min
        return pos

    def _find_next_location(self, change_direction, selected_location, recall_display):
        loc_x, loc_y = self._index2coordinates(selected_location)
        # check what's the max some one has moved in each direction
        for direction in change_direction:
            if direction in [self.direction_keys['left'],
                             self.direction_keys['right']]:
                loc_x += self.direction_values[direction]
                # chek if it's the edge
                loc_x = self._check_edge(loc_x, "x")
            elif direction in [self.direction_keys['up'],
                               self.direction_keys['down']]:
                loc_y += self.direction_values[direction]
                # chek if it's the edge
                loc_y = self._check_edge(loc_y, "y")
            else:
                pass
        selected_location = self._coordinates2index(loc_x, loc_y)
        if selected_location != int(recall_display):
            return selected_location

        # if the selected grid is on the display and on the edge, don't move
        # if the selection is on the display and in the middle, skip the cell
        if direction in [self.direction_keys['left'],
                         self.direction_keys['right']]:
            if loc_x in [0, self.grid_size[0] - 1]:  # on the edge
                loc_x -= self.direction_values[direction]  # don't move
            else:
                loc_x += self.direction_values[direction]  # move past the cell
        elif loc_y in [0, self.grid_size[-1] - 1]:  # on the edge
            loc_y -= self.direction_values[direction] # don't move
        else:
            loc_y += self.direction_values[direction] # move past the cell
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
