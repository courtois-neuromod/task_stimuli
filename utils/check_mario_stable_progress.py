import glob, pandas
for sub in [1,2,3,5, 6]:
    print(f"sub-{sub:02}" + '#'*50)
    ev_fnames = glob.glob(f"sub-{sub:02d}/ses-*/*task-mario_*_events.tsv")
    evs = [pandas.read_csv(ev_fname,delimiter='\t') for ev_fname in ev_fnames]
    evs_complete = [ev for ev in evs if 'questionnaire-answer' in ev.trial_type.values]
    evs_stable = [ev for ev  in evs_complete if len(ev.level.unique()) > 1 ]
    evs_learning = [ev for ev  in evs_complete if len(ev.level.unique()) == 1 ]
    quest_onset = [ev[ev.trial_type=='questionnaire-value-change'].onset.values for ev in evs_learning]
    levels = pandas.concat([ev[ev.trial_type=='gym-retro_game'].level for ev in evs_learning])
    print("learning phase duration (min)", sum([qo[0] for qo in quest_onset if len(qo)])/60.)

    if len(evs_stable) == 0:
        print("not reached stable phase yet?")
        continue
    quest_onset = [ev[ev.trial_type=='questionnaire-value-change'].onset.values for ev in evs_stable]
    levels = pandas.concat([ev[ev.trial_type=='gym-retro_game'].level for ev in evs_stable])
    print("stable phase duration (min)", sum([qo[0] for qo in quest_onset if len(qo)])/60.)
    print(levels.value_counts())
