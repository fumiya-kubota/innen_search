#coding: utf-8

class Player(object):
    def __init__(self):
        super(Player, self).__init__()
        #転校したりしている可能性がある
        #張本勲を参照
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
        year = date.year - 1 if date.month <=3 and date.day <= 31 else date.year
        if self.birth_year:
            if self.birth_year != year:
                raise
        else:
            self.birth_year = year
            self.birth_date = date
