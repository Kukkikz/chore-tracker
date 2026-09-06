# Chore Tracker — Spec

## Overview
A tool for managing shared household chores in a single household (no login —
pick your name from a list of household members).

## Core Features

1. **Chores & members**
   - A fixed list of household members (name only, no accounts).
   - Chores can be one-off or recurring (e.g. "every Monday", "every 3 days").

2. **Manual assignment**
   - Any member can assign any chore to any member.
   - Assignment can be changed at any time before completion.

3. **Completion & history**
   - Marking a chore done logs who did it and when (visible history).
   - If the chore is recurring, completing it automatically creates the next
     occurrence based on its schedule.

4. **Due dates & overdue flagging**
   - Chores have a due date.
   - Chores past their due date and not yet completed are visually flagged
     as overdue.

## Out of scope for v1
- Multiple households / accounts / login
- Notifications or reminders
- Points, leaderboards, or fairness balancing
- Skip/away toggles or chore swapping