from idd.differ import Differ

class DiffDriver:
    def get_diff(self, a, b, typ):
        d = Differ()
        diffs = []
        if typ == "base":
            diffs = [x for x in d.compare(a, b) if x[0] in ('-', '?', ' ')]
        elif typ == "regressed":
            diffs = [x for x in d.compare(b, a) if x[0] in ('+', '?', ' ')]

        # for i in range(0, len(diffs)):
        #     if diffs[i][0] == "-":
        #         diffs[i] = "<div class='diff deleted'>" + diffs[i] + "</div>"
        #     elif diffs[i][0] == "+":
        #         diffs[i] = "<div class='diff added'>" + diffs[i] + "</div>"
        #     elif diffs[i][0] == " ":
        #         diffs[i] = "<div class='diff equal'>" + diffs[i] + "</div>"
        return diffs
