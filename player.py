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
        self.abstract = None
        self.current_club = None
        self.is_active = False

    def add_team(self, t):
        self.teams.add(t)

    def add_area(self, a):
        self.areas.add(a)

    def set_year(self, y):
        if self.birth_year:
            if self.birth_year != y:
                raise
        else:
            self.birth_year = y
