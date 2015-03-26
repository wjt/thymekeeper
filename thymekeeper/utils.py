from datetime import datetime

def isodate(s):
    return datetime.strptime(s, '%Y-%m-%d').date()

def isomonth(s):
    return datetime.strptime(s, '%Y-%m').date()
