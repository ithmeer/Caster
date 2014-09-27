from dragonfly import (Function, Text, Grammar,BringApp,WaitWindow,Key,  
                       IntegerRef,Dictation,Mimic,MappingRule)
import sys, httplib, json, win32api, win32con,re
from lib import utilities, paths, settings
import natlink
from dragonfly.actions.action_focuswindow import FocusWindow

STRICT_PARSER=re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')

def retrieve(n):
    n = int(n)-1
    Text(send("retrieve", n))._execute()

def scroll(n):#n is the index of the list item to scroll to
    send("scroll", (int(n)-1))
    
def rescan():
    send("rescan","")

def sticky_from_unordered(n, n2):
    n = int(n)-1# index of word in unordered list
    if n<10:
        n=n+10
    n2 = int(n2)-1# index of target slot in sticky list
    send("sticky", n, n2, "")
    
def sticky_copy(n):
    n = int(n)-1# index of target slot in sticky list
    Mimic("copy","one")._execute()
    send("sticky", "1", n, utilities.MULTI_CLIPBOARD["1"])

def add_word():
    Mimic("copy","one")._execute()
    send("add", utilities.MULTI_CLIPBOARD["1"])

def remove_word(n):
    n = int(n)-1
    send("remove", n)

def focus_element():
    FocusWindow(executable="pythonw.exe", title=settings.ELEMENT_VERSION)
#     BringApp("pythonw.exe")._execute()
    WaitWindow(title=settings.ELEMENT_VERSION)._execute()

def search():
    focus_element()
    send("search", None)

def extensions():
    focus_element()
    send("extensions", None)

def trigger_directory_box():
    focus_element()    
    send("trigger_directory_box",None)
    
def filter_strict_request_for_data():
    send("filter_strict_request_for_data",None)
    
def filter_strict_return_processed_data(processed_data):
    send("filter_strict_return_processed_data", processed_data)
    
def send(action_type, data, *more_data):
    try:
        c = httplib.HTTPConnection('localhost', 1337)
        data_to_send={}
        data_to_send["action_type"]=str(action_type)
        if action_type in ["retrieve","sticky","remove","unsticky","scroll"]:
            data_to_send["index"]=data
            if action_type=="sticky":
                data_to_send["sticky_index"]=more_data[0]
                data_to_send["auto_sticky"]=more_data[1]
        elif action_type =="add":
            data_to_send["name"]=data
        elif action_type=="filter_strict_return_processed_data":
            data_to_send["processed_data"]=data
        c.request('POST', '/process', json.dumps(data_to_send))
        response_data = c.getresponse().read()
        if len(response_data)>100:# request for strict mode filtering
            utilities.report("Data returned for strict mode processing... processing and returning ...")
            strict_filter(response_data)
            return None
        else:
            utilities.report(response_data)
            return response_data
    except Exception:
        utilities.report(utilities.list_to_string(sys.exc_info()))
        return "SEND() ERROR"

def strict_filter(response_data):
    directory=json.loads(response_data)
    for f in directory["files"].values():
        acceptably_difficult_to_type=[]
        for name in f["names"]:
            difficult_to_type=word_breakdown(name)
            if difficult_to_type:
                acceptably_difficult_to_type.append(name)
        f["names"]=acceptably_difficult_to_type
    
    send("filter_strict_return_processed_data", json.dumps(directory))
            
def word_breakdown(name):
    global STRICT_PARSER
    found_something_difficult_to_type=False
    capitals_changed_to_underscores =STRICT_PARSER.sub(r'_\1', name).lower()
    broken_by_underscores=capitals_changed_to_underscores.split("_")
    for name_piece in broken_by_underscores:
        if not name_piece=="" and len(name_piece)>1:
            dragon_check=natlink.getWordInfo(name_piece,7)
            if dragon_check==None:# only add letter combinations that Dragon doesn't recognize as words
                found_something_difficult_to_type=True
                break
    return found_something_difficult_to_type

def scan_new():
    focus_element()
    Key("home")._execute()
    
    
#     send_key_to_element("scan_new")

def send_key_to_element(action_type):# for some reason, some events are untriggerable without a keypress it seems, hence this
    try:
        element_hwnd= utilities.get_window_by_title(settings.ELEMENT_VERSION)
        print element_hwnd
    except Exception:
        utilities.report(utilities.list_to_string(sys.exc_info()))
    if action_type=="scan_new":
        win32api.SendMessage(element_hwnd, win32con.WM_KEYDOWN, win32con.VK_HOME, 0)
        win32api.PostMessage(element_hwnd, win32con.WM_KEYUP, win32con.VK_HOME, 0)

def enable_element():
    BringApp("pythonw", r"C:\NatLink\NatLink\MacroSystem\asynch\element_src.py", "shell=True")._execute()
    
def kill():
    send("kill","")

class MainRule(MappingRule):
    mapping = {
    "run element":                  Function(enable_element),
    "kill element":                 Function(kill),
    "scroll to <n>":                Function(scroll, extra="n"),
    "get <n>":                      Function(retrieve, extra="n"),
    "sticky list <n> to <n2>":      Function(sticky_from_unordered, extra={"n","n2"}),
    "sticky copy [<n>]":            Function(sticky_copy, extra="n"),
    "add word":                     Function(add_word),
    "remove word <n>":              Function(remove_word, extra="n"),
    "search":                       Function(search),
    "extensions":                   Function(extensions),
    "scan new":                     Function(scan_new),
    "change directory":             Function(trigger_directory_box),
    "rescan directory":             Function(rescan),
    "filter strict":                Function(filter_strict_request_for_data),
    }
    extras = [
              IntegerRef("n", 1, 500),
              IntegerRef("n2", 1, 500),
              Dictation("text"),
             ]
    defaults ={"n": 1,"n2": 1,
               "text": "", 
               }

grammar = Grammar('element')
grammar.add_rule(MainRule())
grammar.load() 