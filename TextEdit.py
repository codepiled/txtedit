import pygame, re, os
from pygame.locals import *
from mouseHandler import *
from keyboardHandler import *
from guiHandler import *
from imageStruct import *

class File:
    def __init__(self, path):
        self.path = path
        self.ext = ""
        self.lines = []
        self.parsed = []
        self.loadFile()
        
    def loadFile(self):
        global syntaxDtb
        
        self.ext = self.path.split("/")[-1].split(".")[-1]
        auto = syntaxDtb.isExt(self.ext)
        if auto != -1:
            syntaxDtb.active = syntaxDtb.configs[auto]
        try:
            thisFile = open(self.path, "r")
        except:
            warn("Cannot open " + self.path)
            return
        
        for line in thisFile:
            self.lines.append(line.rstrip("\n"))
        thisFile.close()
        
        for i in self.lines:
            self.parsed.append(self.parseLine(i))
            
    def parseLine(self, line):
        global syntaxDtb
        indeces = []
        keysIn = []
        
        
        exprC = ["",""]
        exprC[0] = "".join(["\\"+x for x in syntaxDtb.active.comt[0]])
        exprC[1] = "".join(["\\"+x for x in syntaxDtb.active.comt[1]])
        
        commentExpr = exprC[0] + "+.*"

        for match in re.finditer(commentExpr, line):

            if match.span()[0] == 0 or (line[match.span()[0] - 1] != "'" and line[match.span()[0] - 1] != '"'):
                indeces.append([match.span()[0]])
                keysIn.append(match.group())

        special = re.findall(r"[\'|\"]+.*?[\'|\"]", line) + re.findall(r"\-?[0-9]+\.?[0-9]*", line)
        for i in range(len(special)):
            cur = []
            for match in re.finditer(special[i], line):
                cur.append(match.span()[0])
            indeces.append(cur)
            keysIn.append(special[i])
                
        found = re.findall(r"\b\w+\b", line)
        final = []
        if len(found) > 0:
            for l in range(len(found)):
                if syntaxDtb.isKeyword(found[l])and found[l] not in keysIn:
                    keysIn.append(found[l])
                    indeces.append(findAll(found[l], line))

        if len(indeces) == 0:
            return [[False, line]]
        
        else:
            final = []
            string = ""
            k = 0
            while k < len(line):
                for j in range(len(indeces)):
                    if k in indeces[j]:
                        if string != "":

                            final.append([False, string])
                        final.append([True, keysIn[j] , syntaxDtb.active.wordColour(keysIn[j])])
                        string = ""
                        k += len(keysIn[j])
                        break
                    
                if k < len(line):
                    string += line[k]
                k += 1
            
            if string != "":
                 final.append([False, string])
        return final
        
    

    def updateLine(self, lineNum):
        parsed = self.parseLine(self.lines[lineNum])
        self.parsed[lineNum] = parsed[:]

    def mergeLines(self, dest, src):
        self.parsed[dest] += self.parsed[src]
        self.lines[dest] += self.lines[src]
        
        del self.parsed[src]
        del self.lines[src]
        for i in range(dest, len(self.lines)):
            self.updateLine(i)
        fontDtb.adjustScale(0)
        
        
    def drawFile(self):
        sideBuff = 0
        buff = 0
        if drawLineN:
            buff = 5
            sideBuff = fontDtb.selected.size(str(len(self.parsed)))[0] + 4
            pygame.draw.rect(screen, [200, 200, 200], [0, top, sideBuff, windh], 0)

        #Screen scope range
        scope = range(cursor / fontDtb.height, ((cursor + windh) / fontDtb.height) \
                      if ((cursor + windh) / fontDtb.height) < len(self.parsed) else len(self.parsed))
        
        for i in scope:
            x = 0
            if drawLineN:
                lineN = fontDtb.selected.render(str(i + 1).rjust(len(str(len(self.parsed)))), 20, [0, 0, 0])
                screen.blit(lineN, [x + 2, i * fontDtb.height - cursor + top])
                x += sideBuff + buff
            
            for j in range(len(textCursors)):
                if textCursors[j].pos[1] == i:
                    pygame.draw.rect(screen, [240, 240, 240], [x, i * fontDtb.height - cursor + top, windw - x - 5, fontDtb.height], 0)
                    break

            for w in range(len(self.parsed[i])):
                if self.parsed[i][w][0]:
                    surface = fontDtb.selected.render(self.parsed[i][w][1], 100, themeDtb.colours[self.parsed[i][w][2]])
                else:
                    surface = fontDtb.selected.render(self.parsed[i][w][1], 100, themeDtb.colours["def"])
                screen.blit(surface, [x, i * fontDtb.height - cursor + top])
                x += fontDtb.selected.size(self.parsed[i][w][1])[0]
                
        if on:
            temp = 0
            if drawLineN:
                temp = 4
            for i in range(len(textCursors)):
                if textCursors[i].pos[1] in scope:
                    cursSlice = self.lines[textCursors[i].pos[1]][:textCursors[i].pos[0]]
                    pygame.draw.rect(screen, [0, 0, 0], [fontDtb.selected.size(cursSlice)[0] + sideBuff + temp, \
                                                         textCursors[i].pos[1] * fontDtb.height + 2 + top - cursor, 2, fontDtb.height - 4], 0)
        
class keyGroup:
    def __init__(self, colour, words):
        self.colour = colour
        self.words = words
    
class highlight:
    def __init__(self, name, path, extenstions):
        self.name = name
        self.path = path
        self.groups = []
        self.comt = ["", ""]
        self.autoExt = extenstions
        self.getData()
        
    def getData(self):
        try:
            config = open(self.path, "r")
        except:
            warn("Cannot open " + self.path)
            return
        contents = []
        line = config.readline().rstrip("\n")
        comments = line
        while line:
            line = config.readline().rstrip("\n")
            contents.append(line)
        config.close()
        cmntSplit = comments.split("|")[-1].split(",")
        self.comt[0] = cmntSplit[0]
        self.comt[1] = cmntSplit[1]
        knownColours = []
        cur = 0
        contents = "".join(contents)
        parsed = re.findall(r'([A-Za-z][^{}]*)', contents)
        parts = []
        curpart = []
        for i in range(0, len(parsed), 2):
            parts.append([re.findall(r"\w+", parsed[i])[0], re.findall(r"\w+", parsed[i + 1])])
            
        for i in range(len(parts)):
            if parts[i][0] not in knownColours:
                knownColours.append(parts[i][0])
                self.groups.append(keyGroup(parts[i][0], parts[i][1]))
            else:
                for word in parts[i][1]:
                    self.groups[knownColours.index(parts[i][0])].words.append(word)

    def wordColour(self, word):
        if isNum(word):
            return "num"
        
        if (word[0] == "'" or word[0] == '"') and\
           (word[-1] == "'" or word[-1] == '"'):
            return "str"
        if word.find(self.comt[0]) == 0:
            return "cmt"
        
        for i in range(len(self.groups)):
            if self.groups[i].words.count(word) > 0:
                return self.groups[i].colour
        return -1

class syntaxDatabase:
    def __init__(self, path):
        self.configs = []
        self.path = path
        if self.getConfigs() == -1:
            del self
            return
        self.active = None

    def getConfigs(self):
        try:
            cList = open(self.path, "r")
        except:
            warn("Cannot open " + self.path)
            return -1
        contents = cList.read()
        cList.close()
        
        for part in contents.split("\n"):
            parts = part.split(" ")
            self.configs.append(highlight(parts[0], parts[1], parts[2:] if len(parts) > 2 else ""))
            
    def isKeyword(self, word):
        for group in self.active.groups:
            if word in group.words:
                return True
        return False

    def isExt(self, extension):
        for i in range(len(self.configs)):
            if extension in self.configs[i].autoExt:
                return i
        return -1

class fontDatabase:
    def __init__(self, path, fontSize):
        self.path = path
        self.fontSize = fontSize
        self.guiSize = 18
        try:
            self.fonts = os.listdir(self.path)
        except:
            warn("Acess Denied to " + self.path)
            return
        
        self.active = 2
        self.guiFont = self.loadFont(self.fonts[0], self.guiSize)
        self.selected = self.loadFont(self.fonts[self.active], self.fontSize)
        self.height = self.selected.size("I")[1]
        self.guiHeight = self.guiFont.size("I")[1]

    def loadFont(self, font, size):
        return pygame.font.Font(self.path + "/" + font, size)

    def setActiveByName(self, name):
        self.active = self.fonts.index(name)
        self.adjustScale(0)
        
    def adjustScale(self, size):
        global bottom, scale
        self.fontSize += size
        self.selected = self.loadFont(self.fonts[self.active], self.fontSize)
        self.height = self.selected.size("I")[1]
        bottom = len(files[openFile].lines) * self.height
        scale = self.height * 3
        
    def updateFont(self):
        self.selected = self.fonts[self.active]

class themeDatabase:
    def __init__(self, paths, name = "default"):
        self.themeNames = []
        for path in paths:
            self.themeNames.append([path] + os.listdir(path))
        self.active = [0, 1]
        self.setActiveByName(name)
    
    def setActiveByName(self, name):
        for i in range(len(self.themeNames)):
            if self.themeNames[i].count(name + ".tme") > 0:
                self.active[0] = i
                self.active[1] = self.themeNames[i].index(name + ".tme")
                self.colours = self.loadTheme(self.themeNames[self.active[0]][0] + "/" + self.themeNames[self.active[0]][self.active[1]])

    def loadTheme(self, path):
        themeFile = open(path)
        line = themeFile.readline().rstrip('\n')
        colours = {}
        while line:
            split = line.split('|')
            if line=="GROUPCOLOURS":
                line = themeFile.readline().rstrip('\n').lstrip('\t')
                while line!="/GROUPCOLOURS":
                    split = line.split('|')
                    colours[split[0]] = map(int,split[1].split(','))
                    line = themeFile.readline().rstrip('\n').lstrip('\t')
            elif split[0]=="LINENUMBERS":
                drawLineN=bool(int(split[1]))
            if split[0]=="BODYFONT":
                fontDtb.setActiveByName(split[1])
            line = themeFile.readline().rstrip('\n')
        themeFile.close()
        return colours
                
class textCursor:
    def __init__(self, pos, index = -1):
        self.pos = pos
        if index == -1:
            self.index = len(textCursors)
        else:
            self.index = index
            
    def update(self):
        if keyboard.keys[K_RIGHT]:
            if self.pos[0] < len(files[openFile].lines[self.pos[1]]):
                self.pos[0] += 1
            elif self.pos[1] < len(files[openFile].lines) - 1:
                self.pos[1] += 1
                self.pos[0] = 0
                
        elif keyboard.keys[K_LEFT]:
            if self.pos[0] > 0:
                self.pos[0] -= 1
            elif self.pos[1] > 0:
                self.pos[1] -= 1
                self.pos[0] = len(files[openFile].lines[self.pos[1]])
                
        if keyboard.keys[K_UP]:
            if self.pos[1] > 0:
                self.pos[1] -= 1
                if self.pos[0] > len(files[openFile].lines[self.pos[1]]) - 1:
                    self.pos[0] = len(files[openFile].lines[self.pos[1]])
            
        elif keyboard.keys[K_DOWN]:
            if self.pos[1] < len(files[openFile].lines):
                if self.pos[1] < len(files[openFile].lines) - 1:
                    self.pos[1] += 1
                    if self.pos[0] > len(files[openFile].lines[self.pos[1]]) - 1:
                        self.pos[0] = len(files[openFile].lines[self.pos[1]])
                    
        if keyboard.string != "":
            
            files[openFile].lines[self.pos[1]] = strInsert(keyboard.string, files[openFile].lines[self.pos[1]], self.pos[0])
            self.pos[0] += len(keyboard.string)
            files[openFile].updateLine(self.pos[1])
            
        if keyboard.keys[K_TAB]:
            files[openFile].lines[self.pos[1]] =  strInsert(" " * tabWidth, files[openFile].lines[self.pos[1]], self.pos[0])
            self.pos[0] += tabWidth
            
            files[openFile].updateLine(self.pos[1])
             
        elif keyboard.keys[K_RETURN]:
            cut = files[openFile].lines[self.pos[1]][self.pos[0]:]
            files[openFile].lines[self.pos[1]] = files[openFile].lines[self.pos[1]][:self.pos[0]]
            files[openFile].lines.insert(self.pos[1] + 1, cut)
            files[openFile].parsed.insert(self.pos[1] + 1, files[openFile].parseLine(cut))
            files[openFile].updateLine(self.pos[1])

            self.pos[1] += 1
            self.pos[0] = 0

        elif keyboard.keys[K_DELETE]:
            if self.pos[0] < len(files[openFile].lines[self.pos[1]]):
                files[openFile].lines[self.pos[1]] = files[openFile].lines[self.pos[1]][:self.pos[0]] +\
                                                     files[openFile].lines[self.pos[1]][self.pos[0] + 1:]
                files[openFile].updateLine(self.pos[1])
                
            elif self.pos[1] < len(files[openFile].lines):
                files[openFile].mergeLines(self.pos[1], self.pos[1] + 1)
                files[openFile].updateLine(self.pos[1])
                
        elif keyboard.keys[K_BACKSPACE]:
            if self.pos[0] > 0:
                
                files[openFile].lines[self.pos[1]] =  files[openFile].lines[self.pos[1]][:self.pos[0] - 1] +\
                                                       files[openFile].lines[self.pos[1]][self.pos[0]:]
               
                files[openFile].updateLine(self.pos[1])
                self.pos[0] -= 1
                
            elif self.pos[1] > 0:
                
                self.pos[0] = len(files[openFile].lines[self.pos[1] - 1])
                files[openFile].mergeLines(self.pos[1] - 1, self.pos[1])
                files[openFile].updateLine(self.pos[1])
                self.pos[1] -= 1

def warn(string):
    print "warn -", string

def findAll(string, text):
    matches = []
    for match in re.finditer(string , text):
        if not inString(text, match.span()):
            if match.span()[1] < len(text):
                if match.span()[0] == 0 and not isAlpha(text[match.span()[1]]):
                    matches.append(match.span()[0])
                elif not isAlpha(text[match.span()[0] - 1]) and not isAlpha(text[match.span()[1]]):
                    matches.append(match.span()[0])
            elif not isAlpha(text[match.span()[0] - 1]):
                matches.append(match.span()[0])

            elif match.span()[0] == 0 and match.span()[1] == len(text):
                matches.append(match.span()[0])

    return matches

def loadImages(path):
    extWhitelist = ["jpg", "png"]
    images = {}
    try:
        imgList = os.listdir(path)
    except:
        warn("Access Denied to " + path)

    for i in range(len(imgList)):
        name = imgList[i].split(".")[0]
        ext = imgList[i].split(".")[-1]
        if name not in images and ext in extWhitelist:
            images[name] = img(pygame.image.load(path + "/" + imgList[i]).convert_alpha())

    return images

def isAlpha(char):
    return ord(char) in range(97, 123) or\
           ord(char) in range(65, 91)

def isNum(string):
    if string.count("-") > 1:
        return False
    if string.count(".") > 1:
        return False
    return not False in [True if ord(x) in range(48, 58) or x in ('-', '.') else False for x in string]

def inString(text, span):
    left = False
    for i in range(span[0], -1, -1):
        if text[i] == '"':
            left = True
            break
        
    if not left:
        return False
    
    right = True
    for i in range(span[1], len(text)):
        if text[i] == '"':
            right = True
            break

    return right and left

def strInsert(part, string, index):
    return string[:index] + part + string[index:]


global colours, syntaxDtb, fontDtb, screen, cursor, drawLineN,\
       bottom, top, openFile, scale, tabWidth, textCursors, openFile, dtb

pygame.init()
windw, windh = 1900, 980


#Top and bottom boundaries, top variable
top, bottom = 30, 0

#Draw line numbers bool
drawLineN = True

screen = pygame.display.set_mode([windw, windh])

#open file index
openFile = 0

syntaxDtb = syntaxDatabase("manifest.txt")


files = [File("files/textEdit.py"), File("files/highlightTest.py"), File("files/test.py")]

fontDtb = fontDatabase("assets/fonts", 18)
#imgDtb = imageDatabase(["assets/images/GUI"])
themeDtb = themeDatabase(["user/themes/custom", "user/themes/prop"])

#vertical scroll pos
cursor = 0

mouse = Mouse()
keyboard = Keyboard()
textCursors = []
textCursors.append(textCursor([0, 0]))
run = True

fontDtb.adjustScale(0)
scale = 100
pygame.key.set_repeat(250, 30)
clock = pygame.time.Clock()

guiComponents = guiManager(loadImages("assets/images/GUI"))
guiComponents.setFont(fontDtb.guiFont)
guiComponents.addItem(DropDown([windw - 300, 0], [200, 26], [x.split(".")[0] for x in fontDtb.fonts], fontDtb.active), "fontSelector")
guiComponents.addItem(CheckBox([20, 0], [20, 20], drawLineN), "lnToggle")

#spaces in a tab
tabWidth = 4

#Cursor blink on and off intervals
onInterval = 500
offInterval = 400

time = 0
on = True
while run:
    time += clock.get_time()
    mouse.lastState = mouse.clicked
    for i in range(len(keyboard.keys)):
        keyboard.last[i] = keyboard.keys[i]
        keyboard.keys[i] = False
        
    for event in pygame.event.get():
        if event.type == QUIT:
            run = False

        if event.type == MOUSEBUTTONUP:
            mouse.eventUpdate(event)
            
        if event.type == MOUSEBUTTONDOWN:
            mouse.eventUpdate(event)
            
        if event.type == KEYDOWN:
            if event.key not in keyboard.blackList and len(event.unicode) > 0:
                if ord(event.unicode) in range(32, 127):
                    keyboard.keys[ord(event.unicode)] = True
                
            else:
                keyboard.keys[event.key] = True

            if event.key in keyboard.modifiersK:
                keyboard.modifiers[keyboard.modifiersK.index(event.key)] = True
                
        if event.type == KEYUP:
            if event.key in keyboard.modifiersK:
                keyboard.modifiers[keyboard.modifiersK.index(event.key)] = False
    
        if mouse.buttons[4]:
            if keyboard.modifiers[0]:
                fontDtb.adjustScale(2)
                
            elif  cursor > 0:
                cursor -= scale
                
        elif mouse.buttons[5]:
            if keyboard.modifiers[0]:
                if fontDtb.fontSize - 2  > 2:
                    fontDtb.adjustScale(-2)
                
            elif cursor + windh < bottom + top:
                cursor += scale

    if mouse.buttons[2]:
        if cursor >= 0 and cursor + windh <= bottom + top:
            cursor += (mouse.lastpos[1][1] - mouse.lastpos[0][1]) * 4

    if cursor < 0:
        cursor = 0
    elif cursor + windh > bottom + top and bottom - windh >= 0:
        cursor = bottom - windh + top
        
    
    mouse.update()
    keyboard.buildString()
    if on:
        if time >= onInterval:
            on = not on
            time = 0
    else:
        if time >= offInterval:
            on = not on
            time = 0
            
    if  mouse.clicked and not mouse.lastState and mouse.pos[1] > top:
        xPos = 0
        yPos = (mouse.pos[1] + cursor - top) / fontDtb.height
        nLines = len(files[openFile].lines)
        if yPos > nLines - 1:
            yPos = nLines - 1
            
        nChars = len(files[openFile].lines[yPos])
        #-4 hard coded value to align cursor better
        charX = -4
        
        if drawLineN:
            charX = fontDtb.selected.size(str(nLines))[0]
            
        sliceMetrics = fontDtb.selected.metrics(files[openFile].lines[yPos])
        picked = False
        for i in range(nChars):
            if pygame.Rect(mouse.pos[0], mouse.pos[1] + cursor - top, 1, 1).colliderect(pygame.Rect(charX, yPos * fontDtb.height, sliceMetrics[i][4], fontDtb.height)):
                xPos = i
                picked = True
                break
            charX += sliceMetrics[i][4]
            
        if not picked and xPos == 0 and i == nChars - 1:
            xPos = nChars

        textCursors[0].pos[0] = xPos
        textCursors[0].pos[1] = yPos
    
    for i in range(len(textCursors)):
        textCursors[i].update()

    guiComponents.update(mouse)
        
    drawLineN = guiComponents.items["lnToggle"].state
    if guiComponents.items["fontSelector"].newSelection() and guiComponents.items["fontSelector"].selected != -1:
        fontDtb.active = guiComponents.items["fontSelector"].selected
        fontDtb.adjustScale(0)

    screen.fill([255, 255, 255])
    files[openFile].drawFile()

    #Draw top bar
    pygame.draw.rect(screen, [255, 255, 255], [0, 0, windw, top], 0)
    
    #Draw all gui items
    guiComponents.draw(screen)
        
    pygame.display.update()
    clock.tick()
pygame.quit()
