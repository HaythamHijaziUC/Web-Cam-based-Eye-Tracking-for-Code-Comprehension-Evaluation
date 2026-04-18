from collections import Counter

class GazeLogger:
    def __init__(self, warmup_frames=30, min_fixation_frames=8, fps=30.0):
        self.warmup_frames = warmup_frames
        self.min_fixation_frames = min_fixation_frames
        self.fps = fps

        self.frame_index = 0
        self.current_region = None
        self.current_count = 0

        # total frames per region
        self.region_frames = Counter()

        # number of fixations per region
        self.region_fixations = Counter()

        # sequence of fixations (for regression detection)
        self.fixation_sequence = []

    def log_region(self, region_name):
        self.frame_index += 1

        # ignore startup noise
        if self.frame_index < self.warmup_frames:
            return

        if region_name == self.current_region:
            self.current_count += 1
        else:
            # finalize previous fixation
            if self.current_region is not None and self.current_count >= self.min_fixation_frames:
                self.region_frames[self.current_region] += self.current_count
                self.region_fixations[self.current_region] += 1
                self.fixation_sequence.append(self.current_region)

            # start new fixation
            self.current_region = region_name
            self.current_count = 1

    def summarize(self):
        # finalize last fixation
        if self.current_region is not None and self.current_count >= self.min_fixation_frames:
            self.region_frames[self.current_region] += self.current_count
            self.region_fixations[self.current_region] += 1
            self.fixation_sequence.append(self.current_region)

        # convert frames → seconds
        region_seconds = {
            region: frames / self.fps
            for region, frames in self.region_frames.items()
        }

        # regressions: going from higher region index to lower
        region_order = {"Region 1": 1, "Region 2": 2, "Region 3": 3}
        regressions = Counter()

        for i in range(1, len(self.fixation_sequence)):
            prev_r = self.fixation_sequence[i - 1]
            curr_r = self.fixation_sequence[i]
            if region_order[curr_r] < region_order[prev_r]:
                regressions[curr_r] += 1

        return region_seconds, self.region_fixations, regressions
