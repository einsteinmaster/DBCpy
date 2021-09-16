import cantools
from MyDbcReader import fix_dbc, MsgCString, _filter, _map

#dbm = read_dbc("CAN1_Diagnose.dbc")
dbc = cantools.database.load_file(fix_dbc("CAN1_Diagnose.dbc"))

_ml = _filter(lambda x: x.frame_id == 0x18FF3103,dbc.messages)
for m in _map(lambda x: MsgCString(x),_ml):
    print(m+"\n")

from Gui import Gui

mgui = Gui()
mgui.exec()

#cantools.database.dump_file(dbc, 'test_write.dbc')