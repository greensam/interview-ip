#! /usr/bin/env python

import os
import pandas as pd
import numpy as np
from pulp import * 

DOC_NAME = 'Full-Pref-Excel.xlsx'

def solve_assignment(df1, df2):

    cnames = np.concatenate([df1.ix[:, 2:].columns.values, df2.ix[:, 2:].columns.values])

    matrix = df1.ix[:, 2:].as_matrix()
    matrix_round2 = df2.ix[:, 2:].as_matrix()

    print matrix_round2.shape[1]

    prob = LpProblem("Scheduling Feasibility", LpMinimize)

    prob += 1

    people = [i for i in range(matrix.shape[0])]
    times = [i for i in range(matrix.shape[1])]
    round2_times = [i + len(times) for i in range(matrix_round2.shape[1])]

    assign_vars = LpVariable.dicts("AssignedTo", [(i,j) for i in people for j in times + round2_times],   
                                    0, 1,
                                    LpBinary)

    slot_used = LpVariable.dicts("SlotUsed", times + round2_times, 0, 1, LpBinary)

    # require that every person occupies between 11 and 13 slots
    for person in people:
        prob += lpSum([assign_vars[(person, time)] for time in times]) >= 7
        prob += lpSum([assign_vars[(person, time)] for time in times]) <= 9

        prob += lpSum([assign_vars[(person, time)] for time in round2_times]) >= 4
        prob += lpSum([assign_vars[(person, time)] for time in round2_times]) <= 5


        # prob += lpSum([assign_vars[(person, time)] for time in times + round2_times]) >= 12

    for time in times + round2_times:
        for person in people:
            # enforce that slot is marked used if someone is assigned
            prob += slot_used[time] >= assign_vars[(person, time)]

        # enforce that if a slot is assigned, it's assigned to at least 2 people
        prob += lpSum([assign_vars[(person, time)] for person in people]) >= 2*slot_used[time]

        # enforce that a slot is assigned to no more than 2 people
        # (so that if it's assigned, it's assigned to exactly 2)
        prob += lpSum([assign_vars[(person, time)] for person in people]) <= 2

    # make sure people are only assigned to times their available
    for person in people:
        # round 1 constraint
        for time in times:
            prob += assign_vars[(person, time)] <= int(matrix[person, time])

        # round 2 constraint
        for time in round2_times:
            prob += assign_vars[(person, time)] <= int(matrix_round2[person, time - len(times)])

    prob += lpSum(slot_used[t] for t in times) >= 120
    prob += lpSum(slot_used[t] for t in round2_times) >= 60

    prob.solve()

    print "STATUS:", LpStatus[prob.status]

    total = 0
    for person in people:
        ptot = sum(assign_vars[(person, time)].varValue for time in times + round2_times)
        print "person {}".format(person), ptot
        total += ptot

    # for time in times + round2_times: 
    #     print "slot {}".format(time), slot_used[time], sum(assign_vars[(person, time)].varValue for person in people)

    print "total people-slots", total
    print "round 1 slots: {}".format(sum(slot_used[time].varValue for time in times))
    print "round 2 slots: {}".format(sum(slot_used[t].varValue for t in round2_times))

    r1_assignments = np.array([[assign_vars[(person, time)].varValue for time in times] for person in people])
    r2_assignments = np.array([[assign_vars[(person, r2time)].varValue for r2time in round2_times] for person in people])


    outdf = pd.DataFrame(np.hstack([r1_assignments, r2_assignments]))
    print len(cnames), outdf.shape

    outdf.index = df1['EmailAddress']
    outdf.columns = cnames
    outdf.to_csv('assignment.csv')


if __name__ == '__main__':
    
    if not os.path.exists(DOC_NAME):
        print "usage: ./assign.py"
        print "Excel document `Full-Pref-Excel.xlsx` expected in same folder as assign.py."

    dat_round1 = pd.read_excel(DOC_NAME, sheetname='Round 1').fillna(0)
    dat_round2 = pd.read_excel(DOC_NAME, sheetname='Round 2').fillna(0)
    solve_assignment(dat_round1, dat_round2)






