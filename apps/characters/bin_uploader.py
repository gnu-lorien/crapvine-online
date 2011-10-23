import struct
from reversion import revision

from uploader import create_base_vampire, read_experience_entry, read_traitlist_properties, read_trait

import datetime
import math
days_offset = 25569

def read_date(f):
    #return convert_date(struct.unpack("<Q", f.read(8))[0]).strftime("%m/%d/%Y")
    #return struct.unpack("<Q", f.read(8))[0]
    return convert_date(struct.unpack("<d", f.read(8))[0])

def convert_date(vbt):
    base_vb = datetime.datetime(1899, 12, 30, 0, 0, 0, 0)
    just_days = math.floor(vbt)
    seconds = 86400 * (vbt % 1)
    td = datetime.timedelta(days=just_days, seconds=seconds)
    #print "days:", just_days, "seconds:", seconds
    t = base_vb + td
    try:
        if seconds == 0:
            time_string = t.strftime("%m/%d/%Y")
        else:
            time_string = t.strftime("%m/%d/%Y %I:%M:%S %p")
    except ValueError:
        time_string = t.time().strftime("%I:%M:%S %p")
    return time_string

def read_string(f):
    n = read_length(f)
    if n > 0:
        return struct.unpack("<%ds" % n, f.read(n))[0]
    else:
        return ''

def read_boolean(f):
    return struct.unpack("<h", f.read(2))[0]

def read_single(f):
    return struct.unpack("<f", f.read(4))[0]

def read_long(f):
    return struct.unpack("<L", f.read(4))[0]

def read_length(f):
    return struct.unpack("<h", f.read(2))[0]

def read_int(f):
    return read_length(f)

def read_has(f):
    return read_length(f) >= 1

def read_trait_list(f):
    thisList =  {
        'name': read_string(f),
        'abc': read_boolean(f),
        'atomic': read_boolean(f),
        'negative': read_boolean(f),
        'display': read_long(f),
    }

    n = read_length(f)
    thisList['list'] = []
    for i in xrange(n):
        thisList['list'].append({
            'name': read_string(f),
            'val': read_string(f),
            'note': read_string(f),
        })
    return thisList

def read_experience_history(f):
    retdict = {}
    retdict['experience'] = {
        'unspent': read_single(f),
        'earned': read_single(f)
    }
    n = read_length(f)
    experience_entries = []
    for i in xrange(n):
        experience_entries.append({
            'date': read_date(f),
            'change': read_single(f),
            'type': read_long(f),
            'reason': read_string(f),
            'earned': read_single(f),
            'unspent': read_single(f),
        })
    retdict['experience_entries'] = experience_entries
    return retdict

def read_vampire(f):
    vampire = {}
    vampire['attrs'] = {
       'name': read_string(f),
       'nature': read_string(f),
       'demeanor': read_string(f),
       'clan': read_string(f),
       'sect': read_string(f),
       'coterie': read_string(f),
       'sire': read_string(f),
       'generation': read_int(f),
       'title': read_string(f),
       'blood': read_int(f),
       'tempblood': read_int(f),
       'willpower': read_int(f),
       'tempwillpower': read_int(f),
       'conscience': read_int(f),
       'tempconscience': read_int(f),
       'selfcontrol': read_int(f),
       'tempselfcontrol': read_int(f),
       'courage': read_int(f),
       'tempcourage': read_int(f),
       'path': read_string(f),
       'pathtraits': read_int(f),
       'temppathtraits': read_int(f),
       'aura': read_string(f),
       'aurabonus': read_string(f),
       'physicalmax': read_int(f),
       'socialmax': read_int(f),
       'mentalmax': read_int(f),
       'player': read_string(f),
       'status': read_string(f),
       'id': read_string(f),
       'startdate': read_date(f),
       'narrator': read_string(f),
       'npc': read_int(f),
       'lastmodified': read_date(f),
    }
    #print "Reading", vampire['attrs']['name']

    # Experience
    experience_entries_dict = read_experience_history(f)
    vampire['experience'] = experience_entries_dict['experience']
    vampire['experience_entries'] = experience_entries_dict['experience_entries']

#   for i in xrange(n):
#       if experience_entries[i]['date'] != experience_entries[i]['reason']:
#           print i
#           pprint(experience_entries[i])
#           break

    trait_lists = []
    for i in xrange(20):
        trait_lists.append(read_trait_list(f))

    vampire['trait_lists'] = trait_lists

    # Boons
    n = read_length(f)
    boons = []
    for i in range(n):
        boons.append({
            'type': read_string(f),
            'partner': read_string(f),
            'owed': read_boolean(f),
            'date': read_date(f),
            'description': read_string(f),
        })

    vampire['biography'] = read_string(f)
    vampire['biography'] = vampire['biography'].replace('\r\n', '\n')
    vampire['notes'] = read_string(f)
    vampire['notes'] = vampire['notes'].replace('\r\n', '\n')

    return vampire

def is_binary(f):
    binary_header_n = f.read(2)
    binary_header_n = struct.unpack("<h", binary_header_n)[0]
    if binary_header_n != 4:
        return False
    if binary_header_n > 0:
        binary_header = f.read(binary_header_n)
        binary_header = struct.unpack("<%ds" % binary_header_n, binary_header)[0]
        binary_headers = ['GVBE', 'GVBG']
        if binary_header not in binary_headers:
            return False
    return True

def base_read(f):
    binary_header_n = f.read(2)
    binary_header_n = struct.unpack("<h", binary_header_n)[0]
    if binary_header_n > 0:
        binary_header = f.read(binary_header_n)
        binary_header = struct.unpack("<%ds" % binary_header_n, binary_header)[0]
    else:
        binary_header = ''
    #print binary_header
    version = f.read(8)
    version = struct.unpack('<d', version)
    #print version

    has_calendar = read_has(f)
    if has_calendar:
        last_modified = read_date(f)
        calendar_entries_n = read_length(f)
        calendar_entries = []
        for i in xrange(calendar_entries_n):
            calendar_entries.append({
                'date': read_date(f),
                'time': read_string(f),
                'place': read_string(f),
                'notes': read_string(f)
            })

    has_apr_settings = read_has(f)
    if has_apr_settings:
        apr_attrs = {
            'personalactions': read_int(f),
            'addcommon': read_boolean(f),
            'carryunused': read_boolean(f),
            'publicrumors': read_boolean(f),
            'personalrumors': read_boolean(f),
            'racerumors': read_boolean(f),
            'grouprumors': read_boolean(f),
            'subgrouprumors': read_boolean(f),
            'influencerumors': read_boolean(f),
            'previousrumors': read_boolean(f),
            'copyprevious': read_boolean(f),
        }
        background_actions = read_trait_list(f)
        actions_per_level = read_trait_list(f)

    xp_awards_n = read_length(f)
    if xp_awards_n != 0:
        for i in range(xp_awards_n):
            xp_award = {
                'use': read_string(f),
                'name': read_string(f),
                'type': read_long(f),
                'change': read_single(f),
                'reason': read_string(f),
            }

    template_settings_n = read_length(f)
    if template_settings_n != 0:
        for i in range(template_settings_n):
            template_setting = {
                'name': read_string(f),
                'sheet': read_boolean(f),
                'text': read_string(f),
                'rtf': read_string(f),
                'html': read_string(f),
            }

    players_n = read_length(f)
    if players_n != 0:
        players = []
        for i in range(players_n):
            player = {
                'name': read_string(f),
                'id': read_string(f),
                'email': read_string(f),
                'phone': read_string(f),
                'position': read_string(f),
                'status': read_string(f),
                'lastmodified': read_date(f),
            }
            read_experience_history(f)
            player['address'] = read_string(f)
            player['notes'] = read_string(f)

    creature_count = read_int(f)
    creatures = []
    for i in xrange(creature_count):
        creature_type = read_int(f)
        if creature_type == 2:
            creatures.append(read_vampire(f))

    """ We safely ignore the following sections since they come after the characters we care about:
    queries
    items
    rotes
    locations
    actions
    plots
    rumors
    """

    return creatures

@revision.create_on_success
def handle_sheet_upload(uploaded_file, user):
    creatures = base_read(uploaded_file)
    class BinUploadResponse(object):
        pass
    ret = BinUploadResponse()
    ret.vampires = {}
    for c in creatures:
        # Stuck on vampies for now
        current_vampire = create_base_vampire(c['attrs'], user)
        previous_entry = None
        for ee in c['experience_entries']:
            previous_entry = read_experience_entry(ee, current_vampire, previous_entry)

        for tl in c['trait_lists']:
            traits = tl['list']
            del tl['list']
            read_traitlist_properties(tl, current_vampire)
            for i, t in enumerate(traits):
                read_trait(t, tl, current_vampire, i)

        current_vampire.biography = c['biography']
        current_vampire.notes = c['notes']
        current_vampire.update_experience_total()
        current_vampire.save()
        ret.vampires[current_vampire.name] = current_vampire
    return ret
