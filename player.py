#coding: utf-8
from datetime import datetime

class Player(object):
    def __init__(self):
        super(Player, self).__init__()
        #転校したりしている可能性がある
        #張本勲を参照
        self.label = None
        self.cname = None
        self.highschool = set()
        self.college = set()
        self.pro = set()
        self.others = set()
        self.areas = set()
        self.birth_year = None
        self.birth_date = None
        self.abstract = None
        self.current_club = None
        self.is_active = False

    def add_team(self, t):
        self.teams.add(t)

    def add_area(self, a):
        self.areas.add(a)

    def set_birth_date(self, date):
        year = date.year - 1 if date < datetime(date.year, 4, 2) else date.year
        if self.birth_year:
            if self.birth_year != year:
                raise
        else:
            self.birth_year = year
            self.birth_date = date
            return str(year)

    def dump(self, k):
        dump_data = {
            'cname': self.cname,
            'label': k,
            'highschool': tuple(self.highschool),
            'college': tuple(self.college),
            'pro': tuple(self.pro),
            'others': tuple(self.others),
            'areas': tuple(self.areas),
            'birth_date': '{}-{}-{}'.format(self.birth_date.year, self.birth_date.month, self.birth_date.day) if self.birth_date else None,
            'abstract': self.abstract,
            'current_club': self.current_club,
            'is_active': self.is_active
        }
        if hasattr(self, 'label_end'):
            dump_data['label_end'] = self.label_end
        return dump_data

def player_from_dict(data):
    pl = Player()
    pl.cname = data.get('cname')
    pl.highschool = data.get('highschool')
    pl.college = data.get('college')
    pl.pro = data.get('pro')
    pl.others = data.get('others')
    pl.areas = data.get('areas')
    pl.birth_date = datetime.strptime(data.get('birth_date'), '%Y-%m-%d') if data['birth_date'] else None
    pl.abstract = data.get('abstract')
    pl.current_club = data.get('current_club')
    pl.is_active = data.get('is_active')
    if 'label_end' in data:
        pl.label_end = data['label_end']
    if pl.birth_date:
        year = pl.birth_date.year - 1 if pl.birth_date < datetime(pl.birth_date.year, 4, 2) else pl.birth_date.year
        pl.birth_year = year
    return pl
