import re

class Board(object):
    def __init__(self, photoFile):
        with open(photoFile) as inFile:
            self.filename = inFile.readline()
        groups = re.match(r'(.*)IMG-(?P<year>....)-(?P<month>.*)-(?P<day>.*) (?P<hours>.*)h(?P<minutes>.*)m(?P<seconds>.*)s_(?P<battery>.*)%.jpg', self.filename)
        
        try:
            self.year = int(groups.group("year"))
            self.month = int(groups.group("month"))
            self.day = int(groups.group("day"))

            self.hours = int(groups.group("hours"))
            self.minutes = int(groups.group("minutes"))
            self.seconds = int(groups.group("seconds"))

            self.battery = int(groups.group("battery"))
        
        except (AttributeError, ValueError):
            eprint("The format of the screenshot name file is incorrect. Please reconfigure.")

    def __str__(self):
        return  f"Year:    {self.year}\n" \
                f"Month:   {self.month}\n" \
                f"Day:     {self.day}\n" \
                f"Hours:   {self.hours}\n" \
                f"Minutes: {self.minutes}\n" \
                f"Seconds: {self.seconds}\n" \
                f"Battery: {self.battery}"
               