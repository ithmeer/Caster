from castervoice.lib.ctrl.mgr.rule_details import RuleDetails
from castervoice.lib.const import CCRType
from castervoice.asynch.mouse import grids

import win32api, win32con

# Command to kill the grid
def kill():
    control.nexus().comm.get_com("grids").kill()

# Perform an action based on the passed in action number
# action - optional mouse action after movement
def perform_mouse_action(action):
    if action == 1:
        Mouse("left").execute()
    if action == 2:
        Mouse("left:2").execute()
    elif action == 3:
        Mouse("right").execute()

# Command to move the mouse
# n - square to move to
# s - optional inner square to move to
# action - optional mouse action after movement
def move_mouse(n, s, action):
    sudoku = control.nexus().comm.get_com("grids")

    sudoku.move_mouse(int(n), int(s))

    # Close the grid window
    sudoku.kill()
    grids.wait_for_death(settings.SUDOKU_TITLE)
    time.sleep(0.1)

    perform_mouse_action(int(action))

# Command to drag the mouse from the current position
# n0 - optional square to drag from
# s0 - optional inner square to drag from
# n  - square to drag to
# s  - optional inner square to drag to
# action - optional mouse action after movement
def drag_mouse(n0, s0, n, s, action):
    sudoku = control.nexus().comm.get_com("grids")
    x, y = sudoku.get_mouse_pos(int(n), int(s))

    # If dragging from a different location, move there first
    if int(n0) > 0:
        sudoku.move_mouse(int(n0), int(s0))

    sudoku.kill()
    grids.wait_for_death(settings.SUDOKU_TITLE)
    time.sleep(0.1)

    # Hold down click, move to drag destination, and release click
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)
    win32api.SetCursorPos((int(x), int(y)))
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)

    perform_mouse_action(int(action))

'''
Rules for sudoku grid. We can either move the mouse or drag it.
The number n is one of the numbered squares.
The grid portion is a number from 1-9 referencing an inner unnumbered square.
'''
class SudokuGridRule(MergeRule):
    pronunciation = "sudoku grid"

    mapping = {
        "<n> [grid <s>] [<action>]":
            R(Function(move_mouse)),
        "[<n0>] [grid <s0>] drag <n> [grid <s>] [<action>]":
            R(Function(drag_mouse)),
        "escape":
            R(Function(kill)),
        SymbolSpecs.CANCEL:
            R(Function(kill)),
    }
    extras = [
        IntegerRefST("n", -1, 999),
        IntegerRefST("n0", -1, 999),
        IntegerRefST("s", 0, 10),
        IntegerRefST("s0", 0, 10),
        Choice("action", {
            "move": 0,
            "click": 1,
            "double click": 2,
            "right click": 3,
        }),
    ]
    defaults = {
        "n": 0,
        "n0": 0,
        "s": 0,
        "s0": 0,
        "action": 0,
    }

def get_rule():
    details = RuleDetails(title="sudokugrid", ccrtype=CCRType.APP)
    return SudokuGridRule, details
