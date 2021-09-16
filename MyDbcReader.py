class Sig:
    def __init__(self,name,mulId,startBit,length,endian,signed,factor,offset,_min,_max,unit,nodes):
        self.name = name
        self.mulId = mulId
        self.startBit = startBit
        self.length = length
        self.endian = endian
        self.signed = signed
        self.factor = factor
        self.offset = offset
        self._min = _min
        self._max = _max
        self.unit = unit
        self.nodes = nodes
    def __str__(self):
        return self.name
    def __repr__(self):
        return str(self)

class Msg:
    def __init__(self,_id,name,dlc,node):
        self._id = _id
        self.name = name
        self.dlc = dlc
        self.node = node
        self.sigs = []
    def __str__(self):
        return self.name
    def __repr__(self):
        return str(self)
    def getExtId(self):
        return (0x7FFFFFFF) & self._id
    def getPgn(self):
        return ((0xFFFF00) & self._id) >> 8

class DBC:
    def __init__(self):
        self.msgs = []
    def getAllSigs(self):
        sigs = []
        for m in self.msgs:
            sigs += m.sigs
        return list(set(sigs))
    
def splitline(line):
    line = line.strip()
    if len(line) == 0:
        return []
    elems = []
    buffer = [' ']*len(line)
    bLen = 0
    quoteCount = 0
    for c in line:
        if c == '\"':            
            quoteCount += 1
        elif quoteCount % 2 == 0 and c == ' ':
            elems.append("".join(buffer[:bLen]))
            bLen = 0
        else:
            buffer[bLen] = c
            bLen += 1
    if bLen > 0:
        elems.append("".join(buffer[:bLen]))
        bLen = 0
    return elems

MSG_CMD = "BO_"
SIG_CMD = "SG_"

def parse_msg_head(line):
    splt = splitline(line)
    argNr = 0
    for w in splt:
        if argNr == 0 and w == MSG_CMD:
            pass
        elif argNr == 0:
            argNr += 1
            _id = int(w)
        elif argNr == 1:
            argNr += 1
            name = w.replace(':','')
        elif argNr == 2:
            argNr += 1
            dlc = int(w)
        elif argNr == 3:
            argNr += 1
            node = w
    if argNr == 4:
        return Msg(_id,name,dlc,node)
    else:
        print("Could not create message. Too less args ("+str(argNr)+"). Original: \'"+l+"\'")
        return None
def parse_sig(line):
    splt = splitline(line)
    argNr = 0
    nodes = []
    for w in splt:
        if argNr == 0 and w == SIG_CMD:
            pass
        elif argNr == 0:
            argNr += 1
            name = w
        elif argNr == 1 and w == ":":
            argNr += 1
            mulId = None
        elif argNr == 1 and (w.startswith("m") or w.startswith("M")):
            argNr += 1
            mulId = w[1:]
        elif argNr == 2 and w == ":":
            pass
        elif argNr == 2 and '|' in w and '@' in w:
            argNr += 4
            a2345sp = w.split('|')
            startBit = int(a2345sp[0])
            a345sp = a2345sp[1].split('@')
            length = int(a345sp[0])
            endian = "le" if a345sp[1][0] == '1' else "be"
            signed = a345sp[1][1] == '-'
        elif argNr == 6 and w.startswith('(') and w.endswith(')') and ',' in w:
            argNr += 2
            a67sp = w.replace('(','').replace(')','').split(',')
            factor = float(a67sp[0])
            offset = float(a67sp[1])
        elif argNr == 8 and w.startswith('[') and w.endswith(']') and '|' in w:
            argNr += 2
            a89sp = w.replace('[','').replace(']','').split('|')
            _min = float(a89sp[0])
            _max = float(a89sp[1])
        elif argNr == 10:
            argNr += 1
            unit = w
        elif argNr >= 11:
            argNr += 1
            nodes.append(w)
        else:
            print("Error parsing Signal \'"+l+"\' at argNr "+str(argNr)+" and "+w)
            break
    if argNr >= 11:
        return Sig(name,mulId,startBit,length,endian,signed,factor,offset,_min,_max,unit,nodes)        
    else:
        print("Could not create signal. Too less args ("+str(argNr)+"). Original: \'"+l+"\'")
        return None
    
def is_msg_head(l):
    return l.strip().split(' ')[0] == (MSG_CMD)
    
def is_sig(l):
    return l.strip().split(' ')[0] == (SIG_CMD)

def read_dbc(filename):
    lastmsg = None
    dbc = DBC()
    lines = list(filter(lambda x: x,map(lambda x: x.replace('\n',''),open(filename,"r",encoding="cp1252").readlines())))
    for l in lines:
        if is_msg_head(l):
            if lastmsg is not None:
                dbc.msgs.append(lastmsg)
            lastmsg = parse_msg_head(l)
        if is_sig(l) and (not (lastmsg is None)):
            sig = parse_sig(l)
            if (not (sig is None)) and (not (lastmsg is None)):
                lastmsg.sigs.append(sig)
    if lastmsg is not None:
        dbc.msgs.append(lastmsg)
    return dbc
    
def MsgMString(msg):    
    os = msg.name + "  " + hex(msg.getExtId())+"  "+str(msg._id) + "\n"
    msg.sigs.sort(key=lambda x: int(x.mulId if x.mulId is not None and len(x.mulId)>0 else 0)*100 + int(x.startBit))
    printMulId = len(list(filter(lambda z: z.mulId is not None,msg.sigs)))>0
    for s in msg.sigs:
        ms = ""
        sps_offset = 0
        if printMulId:            
            ms += str(s.mulId)
            while len(ms) < 5:
                ms += " "
            sps_offset = 5
        ms += "B{}".format(1+(s.startBit//8))
        while len(ms) < (sps_offset + 4):
            ms += " "
        ms += "b{}".format(1+(s.startBit % 8))
        while len(ms) < (sps_offset + 8):
            ms += " "
        ms += (" " if s.length < 10 else "")+str(s.length)
        while len(ms) < (sps_offset + 12):
            ms += " "
        ms += s.name
        os += ms + "\n"
    return os
    
def _filter(f, l):
    return list(filter(f,l))
def _map(f,l):
    return list(map(f,l))

def msg_to_dbc_string(msg):
    s = "BO_ "+str(msg._id)+" "+msg.name+": "+str(msg.dlc)+" "+msg.node+"\r\n"
    for si in msg.sigs:
        s += " SG_ "+si.name+" "
        s += ("M " if si.mulId is not None and len(si.mulId)==0 else "")
        s += ("m"+si.mulId+" " if si.mulId is not None and len(si.mulId)>0 else "")
        s += ": "+str(si.startBit)+"|"+str(si.length)+"@"
        s += ("1" if si.endian == "le" else "0")
        s += ("- " if si.signed else "+ ")
        s += "("+str(si.factor)+","+str(si.offset)+") "
        s += "["+str(si._min)+"|"+str(si._max)+"] "
        s += "\""+si.unit+"\""
        for n in si.nodes:
            s += " "+n  
        s += "\r\n"
    return s

def make_consistent(msg):
    def get_next_overlapping_signal(msg):        
        for s1 in msg.sigs:
            for s2 in msg.sigs:
                if s1 == s2:
                    continue
                if (s1.mulId == s2.mulId
                    and s1.startBit <= s2.startBit 
                    and (s1.startBit + s1.length) > s2.startBit):
                    return s1
        return None
    found_overlapping = True
    while found_overlapping:
        overl_sig = get_next_overlapping_signal(msg)
        if overl_sig is None:
            found_overlapping = False
        else:
            print("Had to remove signal "+str(overl_sig)+" because it overlapped with another signal in this message")
            print(MsgMString(msg))
            msg.sigs.remove(overl_sig)
    signal_len = 0
    for s in msg.sigs:
        signal_len = max(signal_len,s.startBit+s.length)
    signal_len //= 8
    if signal_len > msg.dlc:
        print("Had to increase msg length to "+str(signal_len)+ " because signals didnt fit in")
        print(MsgMString(msg))
        msg.dlc = signal_len
    return msg
    
def fix_dbc(filename_in,filename_out=None,replace_f=make_consistent):
    if filename_out == None:
        filename_out = filename_in.replace(".dbc","_fixed.dbc")
    with open(filename_in, 'r',encoding="cp1252") as fin:
        with open(filename_out, 'w',encoding="cp1252") as fout:                        
            rlines = fin.readlines()
            lastmsg = None
            for l in rlines:                
                if is_sig(l):
                    s = parse_sig(l.replace('\n',''))
                    if (not (s is None)) and (not lastmsg is None):
                        lastmsg.sigs.append(s)
                elif is_msg_head(l):
                    if lastmsg is not None:
                        fout.write(msg_to_dbc_string(replace_f(lastmsg)))    
                    lastmsg = parse_msg_head(l.replace('\n',''))
                else:
                    if lastmsg is not None:
                        fout.write(msg_to_dbc_string(replace_f(lastmsg)))   
                        lastmsg = None
                    fout.write(l)
    return filename_out

from cantools.subparsers.dump import formatting

def MsgCString(msg,layout=False):
    os = msg.name + "  " + hex(msg.frame_id) + "  " + str(msg.frame_id + (0x80000000 if msg.is_extended_frame else 0)) + "\n"
    if layout:
        os += formatting.layout_string(msg) + "\n"
        if msg.is_multiplexed():
            os += formatting.signal_tree_string(msg) + "\n"
    else:
        msg.signals.sort(key=lambda x: int(x.multiplexer_ids[0] if x.multiplexer_ids is not None and len(x.multiplexer_ids) > 0 else 0)*100 + int(x.start))
        for s in msg.signals:
            ms = ""
            sps_offset = 0
            if msg.is_multiplexed():            
                ms += str(s.multiplexer_ids)
                sps_offset = 10
                while len(ms) < sps_offset:
                    ms += " "                
            ms += "B{}".format(1+(s.start//8))
            while len(ms) < (sps_offset + 4):
                ms += " "
            ms += "b{}".format(1+(s.start % 8))
            while len(ms) < (sps_offset + 8):
                ms += " "
            ms += (" " if s.length < 10 else "")+str(s.length)
            while len(ms) < (sps_offset + 12):
                ms += " "
            ms += s.name
            os += ms + "\n"
    return os
        



