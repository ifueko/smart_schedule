import time


class DailyTimeline:
    def __init__(
        self,
        projects=["MIT", "Parfait", "Social Media", "Personal Management", "Self Care"],
        colors=["blue", "black", "red", "green", "pink"],
    ):
        self.events = []
        self.projects = projects

    def add_event(self, project, title, start_time, end_time):
        self.events.append([project, start_time, end_time, title])
        self.events = sorted(self.events, key=lambda x: (x[1], x[2], x[0], x[-1]))

    def find_next_time(self, hours, start=5.0, end=22.0):
        projected_start = start
        while projected_start < end:
            valid = True
            projected_end = projected_start + hours - 1 / 60.0
            for a, start_time, end_time, b in self.events:
                end_time = end_time - 1 / 60.0
                if (projected_start <= start_time and projected_end >= start_time) or (
                    start_time <= projected_start and end_time >= projected_start
                ):
                    valid = False
            if valid:
                return projected_start
            projected_start += 0.25
        return None

    def __str__(self):
        return "\n".join(
            [
                "Event name: {} | Project {} | Time: {} - {}\n".format(
                    title, project, start, finish
                )
                for project, start, finish, title in self.events
            ]
        )
