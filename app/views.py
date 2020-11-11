# views.py

from flask import Flask, render_template, request, g
import sqlite3
from app import app
import math
charID = 0
Username = ""

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect("database.db")
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else [None]) if one else rv

def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier

def abilityScoreMod(num):
    output = int(round_down((num-10)/2))
    if output > -1:
        return "+" + str(output)
    else:
        return str(output)

def ProfBonus(level):
    if level in [0,1,2,3,4]:
        return "+2"
    if level in [5,6,7,8]:
        return "+3"
    if level in [9,10,11,12]:
        return "+4"
    if level in [13,14,15,16]:
        return "+5"
    if level in [17,18,19,20]:
        return "+6"   

def MaxLevelChars():
    return query_db('Select Name from Player where level = (Select MAX(Level) from Player)')

def LeastLevelChar():
    return query_db('Select Name from Player where level = (Select MIN(Level) from Player)')

def dataAverage(value,table):
    return query_db('Select AVG(?) from ? ',(value,table),one=True)

def dataSum(value,table):
    return query_db('Select SUM(?) from ? ',(value,table),one=True)

def addRace(RaceName):
    global charID
    with sqlite3.connect("database.db") as db:
        cur = db.cursor()
        cur.execute("INSERT into IsRace (CharID, RaceName) values (?,?)",(charID,RaceName))
        db.commit()

def addClass(ClassName):
    global charID
    with sqlite3.connect("database.db") as db:
        cur = db.cursor()
        cur.execute("INSERT into IsClass (CharID, ItemID) values (?,?)",(charID,ClassName))
        db.commit()

def deleteRace():
    global charID
    with sqlite3.connect("database.db") as db:
        cur = db.cursor()
        cur.execute("DELETE from IsRace where CharID = ?",(charID,))
        db.commit()

def deleteClass():
    global charID
    with sqlite3.connect("database.db") as db:
        cur = db.cursor()
        cur.execute("DELETE from IsClass where CharID = ?",(charID,))
        db.commit()

def myHash(string):
    if(len(string) % 2 == 0): #If its even, it gets multiplied by 31, odd gets 17
        return sum([ord(c) for c in string])*31
    else:
        return sum([ord(c) for c in string])*17
  
def reloadDashboard():
    global Username
    IDs = query_db('Select CharID from Created Where User = ?',(Username,),one=False)
    
    rows = []
    x = 0
    for charID in IDs:
        rows.append(query_db('Select CharID,Name,Level from Player Where CharID = ?',(charID),one=True))
        rows[x] = rows[x] + (query_db('Select ClassName from IsClass where CharID = ?',(charID),one=True))
        rows[x] = rows[x] + (query_db('Select RaceName from IsRace where CharID = ?',(charID),one=True))
        x += 1
    
    prows = [[],[]]
    prows[0] = query_db('Select Name from Party',())
    idList = []
    for x in range(len(prows[0])):
        prows[1].append([])
        idList = query_db('Select CharID from BelongsTo where PartyName = ?',(prows[0][x][0],))
        for id in idList:
            prows[1][x].append(query_db('Select name,level from Player where CharID = ?',(id[0],)))

    partyAverageLevels = []
    for x in range(len(prows[0])):
        partyAverageLevels.append(0)
        idList = query_db('Select CharID from BelongsTo where PartyName = ?',(prows[0][x][0],))
        for id in idList:
            partyAverageLevels[x] += (query_db('Select Level from Player where CharID = ?',(id[0],)))[0][0]
        if (len(idList)):
            partyAverageLevels[x] /= len(idList)
            partyAverageLevels[x] = round_down(partyAverageLevels[x],2)

    return render_template("dashboard.html", rows = rows, prows = prows, length = len(prows[0]), partyAverageLevels = partyAverageLevels)


def reloadSheet():
    global charID
    #What the player owns
    pa = query_db("Select * from Player where CharID = ?", (charID,), one=True)
    pRaceName = query_db("Select RaceName from isRace where CharID = ?", (charID,), one=True)
    pRace = query_db("Select * from Race where RaceName = ?", (pRaceName), one = True)
    pClassName = query_db("Select ClassName from isClass where CharID = ?", (charID,), one=True)
    pClass = query_db("Select * from Class where Name = ?", (pClassName), one = True)
    
    #Player's Items
    pitems = []
    prepitems = query_db("Select ItemID from OwnsItem where CharID = ?", (charID,))
    if prepitems is None:
        numpitems = 0
    else:
        numpitems = len(prepitems)
        for item in prepitems:
            pitems.append(query_db("select * from Items where ItemID = ?", (item),one=True))
    

    #Player's Melee Weapons
    pmeleeweapons= []
    prepmeleeweapons = query_db("Select WeaponID from OwnsMeleeWeapon where CharID = ?", (charID,))
    if prepmeleeweapons is None:
        numpmeleeweapons = 0
    else:
        numpmeleeweapons = len(prepmeleeweapons)
        for weapon in prepmeleeweapons:
            pmeleeweapons.append(query_db("select * from MeleeWeapon where WeaponID = ?", (weapon),one=True))
    
    #Player's Ranged Weapons
    prangedweapons= []
    preprangedweapons = query_db("Select WeaponID from OwnsRangedWeapon where CharID = ?", (charID,))
    if preprangedweapons is None:
        numprangedweapons = 0
    else:
        numprangedweapons = len(preprangedweapons)
        for weapon in preprangedweapons:
            prangedweapons.append(query_db("select * from RangedWeapon where WeaponID = ?", (weapon),one=True))

    #Player's Spells
    pspells= []
    prepspells = query_db("Select SpellID from OwnsSpell where CharID = ?", (charID,))
    if prepspells is None:
        numpspells = 0
    else:
        numpspells = len(prepspells)
        for spell in prepspells:
            pspells.append(query_db("select * from Spell where SpellID = ?", (spell),one=True))

    #Everything (but not the race and class of the player)
    races = query_db("Select RaceName from Race where RaceName != ? and RaceName != 'ChooseARace'", (pRaceName))
    classes = query_db("Select Name from Class where Name != ? and Name != 'ChooseAClass'", (pClassName))
    items = query_db("Select * from Items")
    meleeweapons = query_db("Select * from MeleeWeapon")
    rangedweapons = query_db("Select * from RangedWeapon")
    spells = query_db("Select * from Spell")
    alignments = ["Lawful Good","Neutral Good","Chaotic Good","Lawful Neutral","True Neutral","Chaotic Neutral","Lawful Evil","Neutral Evil","Chaotic Evil"]

    #Take out the player's alignment
    if pa[3] in alignments:
        alignments.remove(pa[3])
    
    return render_template("sheet.html",
                            all_races = races,
                            all_classes = classes,
                            all_alignments = alignments,
                            all_items = items,
                            all_meleeweapons = meleeweapons,
                            all_rangedweapons = rangedweapons,
                            all_spells = spells,
                            pItems = pitems,
                            pMeleeweapons = pmeleeweapons,
                            pRangedweapons = prangedweapons,
                            pSpells = pspells,
                            numpItems = numpitems,
                            numpMeleeweapons = numpmeleeweapons,
                            numpRangedweapons = numprangedweapons,
                            numpSpells = numpspells,
                            character_name = pa[1],
                            level = pa[4],
                            pRace = pRace[0], 
                            pClass = pClass[0],
                            alignment = pa[3],
                            background = pa[6],
                            darkvision = pRace[3],
                            size = pRace[1],
                            raceAbilities = pRace[5],
                            classAbilities = pClass[2], 

                            allies_and_orgs = pa[2],
                            languages = pa[8],

                            current_health = pa[15],
                            max_health = pa[14],

                            Strength = pa[21],
                            Dexterity = pa[20],
                            Constitution = pa[19],
                            Intelligence = pa[18],
                            Wisdom = pa[17],
                            Charisma = pa[16],
                            StrengthMOD = abilityScoreMod(pa[21]),
                            DexterityMOD = abilityScoreMod(pa[20]),
                            ConstitutionMOD = abilityScoreMod(pa[19]),
                            IntelligenceMOD = abilityScoreMod(pa[18]),
                            WisdomMOD = abilityScoreMod(pa[17]),
                            CharismaMOD = abilityScoreMod(pa[16]),

                            acrobatics = pa[22],
                            animal_handling = pa[23],
                            arcana = pa[24],
                            athletics = pa[25],
                            deception = pa[26],
                            history = pa[27],
                            insight = pa[28],
                            intimidation = pa[29],
                            investigation = pa[30],
                            medicine = pa[31],
                            nature = pa[32],
                            perception = pa[33],
                            performance = pa[34],
                            persuasion = pa[35],
                            religion = pa[36],
                            slight_of_hand = pa[37],
                            stealth = pa[38],
                            survival = pa[39],

                            inspiration = pa[7],
                            passive_perception = pa[5],
                            proficiency_bonus = ProfBonus(pa[4]),
                            hit_dice = pClass[7],

                            saving_strength = pa[40],
                            saving_dexterity = pa[41],
                            saving_constitution = pa[42],
                            saving_wisdom = pa[43],
                            saving_intelligence = pa[44],
                            saving_charisma = pa[45],

                            armor_class = pa[46],
                            initiative = pa[13],
                            speed = pRace[2],

                            personality = pa[11],
                            ideals = pa[12],
                            bonds = pa[10],
                            flaws = pa[9],
                            misc = pa[47]
                            )

@app.route("/") 
def login():
    return render_template("login.html")

@app.route("/dashboard/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/sheet",methods = ["POST","GET"])
def sheet():
    global charID 
    if request.method == "POST":   
        CharID = request.form["id"] 
    charID = CharID 

    return reloadSheet()

@app.route("/BackDashboard",methods = ["POST","GET"])
def BackDashboard():
    return reloadDashboard()

@app.route("/BackLogin",methods = ["POST","GET"])
def BackLogin():
    return render_template("login.html")

@app.route("/search",methods = ["POST","GET"])
def search():
    if request.method == "POST":
        name = request.form["name"]
    name = "%"+name+"%"
    items = query_db("Select ItemName from Items where ItemName like ?",(name,))
    for x in range(len(items)):
        items[x] = items[x] + ("Magical Weapon or Item",)

    mweapons = query_db("Select Weapon from MeleeWeapon where Weapon like ?",(name,))
    for x in range(len(mweapons)):
        mweapons[x] = mweapons[x] + ("Melee Weapon",)

    rweapons = query_db("Select Weapon from RangedWeapon where Weapon like ?",(name,))
    for x in range(len(rweapons)):
        rweapons[x] = rweapons[x] + ("Ranged Weapon",)

    spells = query_db("Select Spell_Name from Spell where Spell_Name like ?",(name,))
    for x in range(len(spells)):
        spells[x] = spells[x] + ("Spell",)
    List = items + mweapons + rweapons + spells
    return render_template("search.html",List=List)

@app.route("/SaveSheet",methods = ["POST","GET"])
def SaveSheet():
    global charID
    if request.method == "POST":
        Strength = request.form["Strength"]
        Dexterity = request.form["Dexterity"]
        Constitution = request.form["Constitution"]
        Intelligence = request.form["Intelligence"]
        Wisdom = request.form["Wisdom"]
        Charisma = request.form["Charisma"]

        character_name = request.form["playerName"]
        level = request.form["level"]
        pRace = request.form["race"]
        pClass = request.form["class"]
        alignment = request.form["alignment"]
        background = request.form["background"]

        allies_and_orgs = request.form["allies_and_orgs"]
        languages = request.form["languages"]

        current_health = request.form["current_health"]
        max_health = request.form["max_health"]
        acrobatics = request.form["acrobatics"]
        animal_handling = request.form["animal_handling"]
        arcana = request.form["arcana"]
        athletics = request.form["athletics"]
        deception = request.form["deception"]
        history = request.form["history"] 
        insight = request.form["insight"]
        intimidation = request.form["intimidation"]
        investigation = request.form["investigation"]
        medicine = request.form["medicine"]
        nature = request.form["nature"]
        perception = request.form["perception"]
        performance = request.form["performance"]
        persuasion = request.form["persuasion"]
        religion = request.form["religion"]
        slight_of_hand = request.form["slight_of_hand"]
        stealth = request.form["stealth"]
        survival = request.form["survival"]

        inspiration = request.form["inspiration"]
        passive_perception = request.form["passive_perception"]
        proficiency_bonus = request.form["proficiency_bonus"]
        hit_dice = request.form["hit_dice"]

        saving_strength = request.form["saving_strength"]
        saving_dexterity = request.form["saving_dexterity"]
        saving_constitution = request.form["saving_constitution"]
        saving_wisdom = request.form["saving_wisdom"]
        saving_intelligence = request.form["saving_intelligence"]
        saving_charisma = request.form["saving_charisma"]

        armor_class = request.form["armor_class"]
        initiative = request.form["initiative"]
        speed = request.form["speed"]

        personality = request.form["personality"]
        ideals = request.form["ideals"]
        bonds = request.form["bonds"]
        flaws = request.form["flaws"]
        misc = request.form["misc"]
    with sqlite3.connect("database.db") as db:
        cur = db.cursor()
        #remove player from IsClass, IsRace
        cur.execute("DELETE from IsClass where CharID = ?",(charID,))
        cur.execute("DELETE from IsRace where CharID = ?",(charID,))
        # add player into IsClass, IsRace based on Form 
        cur.execute("INSERT into isClass (CharID, ClassName) values (?,?)",(charID,pClass))
        cur.execute("INSERT into isRace (CharID, RaceName) values (?,?)",(charID,pRace))
        db.commit()
    


    with sqlite3.connect("database.db") as db:
        cur = db.cursor()
        cur.execute("UPDATE Player Set Strength = ?,"
                                        "Dexterity = ?,"
                                        "Constitution = ?,"
                                        "Intelligence = ?,"
                                        "Wisdom = ?,"
                                        "Charisma = ?,"
                                        "Name = ?,"
                                        "Level = ?,"
                                        "Alignment = ?,"
                                        "Background = ?,"
                                        "AlliesandOrgs = ?,"
                                        "Languages = ?,"
                                        "CurrHP = ?,"
                                        "MaxHP = ?,"
                                        "Acrobatics = ?,"
                                        "AnimalHandling = ?," 
                                        "Arcana = ?,"
                                        "Athletics = ?," 
                                        "Deception = ?,"
                                        "History = ?," 
                                        "Insight = ?," 
                                        "Intimidation = ?,"
                                        "Investigation = ?,"
                                        "Medicine = ?," 
                                        "Nature = ?,"
                                        "Perception = ?,"
                                        "Performance = ?," 
                                        "Persuasion = ?,"
                                        "Religion = ?," 
                                        "SleightofHand = ?," 
                                        "Stealth = ?,"
                                        "Survival = ?,"
                                        "Inspiration = ?," 
                                        "PassivePerception = ?,"
                                        "StrThrow = ?,"
                                        "DexThrow = ?," 
                                        "ConThrow = ?," 
                                        "WisThrow = ?,"
                                        "IntThrow = ?," 
                                        "ChaThrow = ?," 

                                        "ArmorClass = ?,"
                                        "Initative = ?," 

                                        "PersonalityTrait = ?," 
                                        "Ideal = ?,"
                                        "Bond = ?,"
                                        "Flaws = ?,"
                                        "MiscInventory = ? where CharID = ?", \
                                        (Strength, \
                                        Dexterity, \
                                        Constitution, \
                                        Intelligence, \
                                        Wisdom, \
                                        Charisma, \
                                        character_name, \
                                        level, \
                                        alignment, \
                                        background, \
                                        allies_and_orgs, \
                                        languages, \
                                        current_health, \
                                        max_health, \
                                        acrobatics, \
                                        animal_handling, \
                                        arcana, \
                                        athletics, \
                                        deception, \
                                        history, \
                                        insight, \
                                        intimidation, \
                                        investigation, \
                                        medicine, \
                                        nature, \
                                        perception, \
                                        performance, \
                                        persuasion, \
                                        religion, \
                                        slight_of_hand, \
                                        stealth, \
                                        survival, \

                                        inspiration, \
                                        passive_perception, \
                                        saving_strength, \
                                        saving_dexterity, \
                                        saving_constitution, \
                                        saving_wisdom, \
                                        saving_intelligence, \
                                        saving_charisma, \

                                        armor_class, \
                                        initiative, \

                                        personality, \
                                        ideals, \
                                        bonds, \
                                        flaws, \
                                        misc, \
                                        charID))
        db.commit()

    return reloadSheet()
    

    
@app.route("/CreateCharacter", methods = ["POST"])  
def CreateCharacter():
    global Username
    if request.method == "POST": 
        playerName = request.form["name"]
        
    with sqlite3.connect("database.db") as db:
        cur = db.cursor()
        cur.execute("Insert into Player (name,level,Initative,MaxHP,Strength,Dexterity,Constitution,Intelligence,Wisdom,Charisma,Alignment,Acrobatics,AnimalHandling,Arcana,Athletics,Deception,History,Insight,Intimidation,Investigation,Medicine,Nature,Perception,Performance,Persuasion,Religion,SleightofHand,Stealth,Survival,StrThrow,DexThrow,ConThrow,WisThrow,IntThrow,IntThrow,ChaThrow,ArmorClass,CurrHP,Inspiration,PassivePerception) values (?,1,0,0,0,0,0,0,0,0,'True Neutral',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",(playerName,))  
        db.commit()
        newCharID = query_db('Select MAX(CharID) from Player',one=True)

        cur = db.cursor()
        cur.execute("INSERT into Created (User, CharID) values (?,?)",(Username,newCharID[0]))
        cur.execute("INSERT into isClass (CharID, ClassName) values (?,?)",(newCharID[0],"ChooseAClass"))
        cur.execute("INSERT into isRace (CharID, RaceName) values (?,?)",(newCharID[0],"ChooseARace"))
        db.commit()  
    return reloadDashboard()

@app.route("/DeleteCharacter", methods = ["POST"])  
def DeleteCharacter():
    global Username
    if request.method == "POST": 
        id = request.form["id"]
        
    with sqlite3.connect("database.db") as db:  
        cur = db.cursor()

        cur.execute("delete from Player where CharID = ?",(id,))
        cur.execute("delete from Created where CharID = ?",(id,))
        cur.execute("delete from isClass where CharID = ?",(id,))
        cur.execute("delete from isRace where CharID = ?",(id,))
        cur.execute("delete from BelongsTo where CharID = ?",(id,))
        cur.execute("delete from OwnsMeleeWeapon where CharID = ?",(id,))
        cur.execute("delete from OwnsRangedWeapon where CharID = ?",(id,))
        cur.execute("delete from OwnsSpell where CharID = ?",(id,))
        cur.execute("delete from OwnsItem where CharID = ?",(id,))

        db.commit()
    return reloadDashboard()

@app.route("/createparty", methods = ["POST"])  
def CreateParty():
    global Username
    if request.method == "POST": 
        PartyName = request.form["PartyName"]
    with sqlite3.connect("database.db") as db:  
        cur = db.cursor()  
        cur.execute("Insert into Party (name) Values (?)",(PartyName,))  
        db.commit()
    
    return reloadDashboard()
    
@app.route("/delparty", methods = ["POST"])  
def DeleteParty():
    global Username
    if request.method == "POST": 
        PartyName = request.form["PartyName"]
    with sqlite3.connect("database.db") as db:  
        cur = db.cursor()  
        cur.execute("Delete from Party where Name = ?",(PartyName,))
        cur.execute("Delete from BelongsTo where PartyName = ?",(PartyName,))
        db.commit()
    return reloadDashboard()

@app.route("/joinparty", methods = ["POST"])  
def JoinParty():
    global Username
    if request.method == "POST": 
        PartyName = request.form["PartyName"]
        CharID = request.form["id"]
    with sqlite3.connect("database.db") as db:  
        cur = db.cursor()  
        cur.execute("Insert into BelongsTo (PartyName,CharID) Values (?,?)",(PartyName,CharID,))
        db.commit()   
    return reloadDashboard()

@app.route("/leaveparty", methods = ["POST"])  
def LeaveParty():
    global Username
    if request.method == "POST": 
        PartyName = request.form["PartyName"]
        CharID = request.form["id"]
    with sqlite3.connect("database.db") as db:  
        cur = db.cursor()  
        cur.execute("Delete from BelongsTo where PartyName = ? and CharID = ?",(PartyName,CharID,))
        db.commit()   
    return reloadDashboard()

@app.route("/AddItem", methods = ["POST"])
def AddItem():
    global charID
    if request.method == "POST":
        item = request.form["id"]

    with sqlite3.connect("database.db") as db:
        cur = db.cursor()
        cur.execute("INSERT into OwnsItem (CharID, ItemID) values (?,?)",(charID,item))
        db.commit()

    return reloadSheet()

@app.route("/RemoveItem", methods = ["POST"])
def RemoveItem():
    global charID
    if request.method == "POST":
        item = request.form["id"]

    with sqlite3.connect("database.db") as db:
        cur = db.cursor()
        cur.execute("DELETE from OwnsItem where CharID = ? and ItemID = ?",(charID,item))
        db.commit()
    return reloadSheet()

@app.route("/AddMeleeWeapon", methods = ["POST"])
def AddMeleeWeapon():
    global charID
    if request.method == "POST":
        weapon = request.form["id"]

    with sqlite3.connect("database.db") as db:
        cur = db.cursor()
        cur.execute("INSERT into OwnsMeleeWeapon (CharID, WeaponID) values (?,?)",(charID,weapon))
        db.commit()
    
    return reloadSheet()

@app.route("/RemoveMeleeWeapon", methods = ["POST"])
def RemoveMeleeWeapon():
    global charID
    if request.method == "POST":
        weapon = request.form["id"]

    with sqlite3.connect("database.db") as db:
        cur = db.cursor()
        cur.execute("DELETE from OwnsMeleeWeapon where CharID = ? and WeaponID = ?",(charID,weapon))
        db.commit()
    
    return reloadSheet()

@app.route("/AddRangedWeapon", methods = ["POST"])  
def AddRangedWeapon():
    global charID
    if request.method == "POST": 
        weapon = request.form["id"] 

        with sqlite3.connect("database.db") as db:
            cur = db.cursor()
            cur.execute("INSERT into OwnsRangedWeapon (CharID, WeaponID) values (?,?)",(charID,weapon))
            db.commit()
    return reloadSheet()

@app.route("/RemoveRangedWeapon", methods = ["POST"])  
def RemoveRangedWeapon():
    global charID
    if request.method == "POST": 
        weapon = request.form["id"] 

        with sqlite3.connect("database.db") as db:
            cur = db.cursor()
            cur.execute("DELETE from OwnsRangedWeapon where CharID = ? and WeaponID = ?",(charID,weapon))
            db.commit()

    return reloadSheet()

@app.route("/AddSpell", methods = ["POST"])  
def AddSpell():
    global charID
    if request.method == "POST": 
        spell = request.form["id"] 

        with sqlite3.connect("database.db") as db:
            cur = db.cursor()
            cur.execute("INSERT into OwnsSpell (CharID, SpellID) values (?,?)",(charID,spell))
            db.commit()

    return reloadSheet()

@app.route("/RemoveSpell", methods = ["POST"])  
def RemoveSpell():
    global charID
    if request.method == "POST": 
        spell = request.form["id"] 

        with sqlite3.connect("database.db") as db:
            cur = db.cursor()
            cur.execute("DELETE from OwnsSpell where CharID = ? and SpellID = ?",(charID,spell))
            db.commit()

    return reloadSheet()

@app.route("/savedetails",methods = ["POST","GET"])  
def saveDetails():  
    msg = "msg"
    if request.method == "POST":  
        try: 
            email = request.form["email"]  
            username = request.form["username"]  
            password = myHash(request.form["password"])
            with sqlite3.connect("database.db") as db:  
                cur = db.cursor()  
                cur.execute("INSERT into Users (email, username, password) values (?,?,?)",(email,username,password))  
                db.commit()
                newCharID = query_db('Select MAX(CharID) from Player',one=True)  
                msg = "User successfully Added" 
        except:
            db.rollback()
            msg = "We can not add the User to the list"
        finally:
            db.close()
            return render_template("login.html",msg = msg)        

@app.route("/checkdetails",methods = ["POST","GET"])
def checkDetails():
    global Username
    msg = "msg"
    if request.method == "POST":  
        try:
            username = request.form["username"]
            password = myHash(request.form["password"])
            with sqlite3.connect("database.db") as db:
                namecheck = query_db('Select * from Users where username = ? and password = ?', (username,password), one=True)
                if namecheck is None:
                    exit()
                else:
                    Username = username
                    return reloadDashboard()    
        except: 
            msg = "There has been an error! Please Try again!"
            return render_template("login.html",msg=msg)
