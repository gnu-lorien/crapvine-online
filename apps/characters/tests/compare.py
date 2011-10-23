def compare_vampire_base_attributes(self, left, right):
    self.assertEquals(left.nature, right.nature)
    self.assertEquals(left.demeanor, right.demeanor)
    self.assertEquals(left.blood, right.blood)
    self.assertEquals(left.clan, right.clan)
    self.assertEquals(left.conscience, right.conscience)
    self.assertEquals(left.courage, right.courage)
    self.assertEquals(left.generation, right.generation)
    self.assertEquals(left.path, right.path)
    self.assertEquals(left.pathtraits, right.pathtraits)
    self.assertEquals(left.physicalmax, right.physicalmax)
    self.assertEquals(left.sect, right.sect)
    self.assertEquals(left.selfcontrol, right.selfcontrol)
    self.assertEquals(left.willpower, right.willpower)
    self.assertEquals(left.title, right.title)
    self.assertEquals(left.aura, right.aura)
    self.assertEquals(left.coterie, right.coterie)
    self.assertEquals(left.id_text, right.id_text)
    self.assertEquals(left.sire, right.sire)
    self.assertEquals(left.tempcourage, right.tempcourage)
    self.assertEquals(left.tempselfcontrol, right.tempselfcontrol)
    self.assertEquals(left.tempwillpower, right.tempwillpower)
    self.assertEquals(left.tempblood, right.tempblood)
    self.assertEquals(left.tempconscience, right.tempconscience)
    self.assertEquals(left.temppathtraits, right.temppathtraits)

def compare_sheet_base_attributes(self, left, right):
    self.assertEquals(left.home_chronicle, right.home_chronicle)
    self.assertEquals(left.start_date, right.start_date)
    self.assertEquals(left.last_modified, right.last_modified)
    self.assertEquals(left.npc, right.npc)
    self.assertEquals(left.notes, right.notes)
    self.assertEquals(left.biography, right.biography)
    self.assertEquals(left.status, right.status)
    self.assertEquals(left.experience_unspent, right.experience_unspent)
    self.assertEquals(left.experience_earned, right.experience_earned)

def compare_traits(self, left, right):
    left_traits = left.traits.all().order_by('traitlistname__name', 'order')
    right_traits = right.traits.all().order_by('traitlistname__name', 'order')
    for l, r in zip(left_traits, right_traits):
        self.assertEquals(l.value, r.value)
        self.assertEquals(l.note,  r.note)
        self.assertEquals(l.name,  r.name)


def compare_experience_entries(self, left, right):
    left_entries = left.experience_entries.all()
    right_entries = right.experience_entries.all()
    for l, r in zip(left_entries, right_entries):
        self.assertEquals(l.reason,      r.reason)
        self.assertEquals(l.change,      r.change)
        self.assertEquals(l.change_type, r.change_type)
        self.assertEquals(l.earned,      r.earned)
        self.assertEquals(l.unspent,     r.unspent)
        self.assertEquals(l.date,        r.date)

def compare_sheets(self, left, right):
    compare_sheet_base_attributes(self, left, right)
    compare_traits(self, left, right)
    compare_experience_entries(self, left, right)

def compare_vampire_sheets(self, left, right):
    compare_vampire_base_attributes(self, left, right)
    compare_sheet_base_attributes(self, left, right)
    compare_traits(self, left, right)
    compare_experience_entries(self, left, right)