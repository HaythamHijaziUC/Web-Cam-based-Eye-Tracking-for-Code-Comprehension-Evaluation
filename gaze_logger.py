from collections import Counter
import time

class GazeLogger:
    def __init__(self, warmup_frames=30, min_fixation_frames=10, fps=30.0):
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
        # Store objects: {"name": name, "start_line": line}
        self.fixation_sequence = []

    def log_region(self, region_metadata):
        """
        region_metadata: dict with {"name": str, "start": int} or None
        """
        self.frame_index += 1

        # ignore startup noise
        if self.frame_index < self.warmup_frames:
            return

        region_name = region_metadata["name"] if region_metadata else None

        if region_name == self.current_region:
            self.current_count += 1
        else:
            # finalize previous fixation
            if self.current_region is not None and self.current_count >= self.min_fixation_frames:
                self.region_frames[self.current_region] += self.current_count
                self.region_fixations[self.current_region] += 1
                
                # Metadata of the region we just finished
                self.fixation_sequence.append(self.prev_metadata)

            # start new fixation
            self.current_region = region_name
            self.current_count = 1
            self.prev_metadata = region_metadata

    def summarize(self):
        # finalize last fixation
        if self.current_region is not None and self.current_count >= self.min_fixation_frames:
            self.region_frames[self.current_region] += self.current_count
            self.region_fixations[self.current_region] += 1
            self.fixation_sequence.append(self.prev_metadata)

        # convert frames → seconds
        region_seconds = {
            region: frames / self.fps
            for region, frames in self.region_frames.items()
        }

        # regressions: going from a region with a higher line number to a lower one
        regressions = Counter()
        transitions = []

        for i in range(1, len(self.fixation_sequence)):
            prev_meta = self.fixation_sequence[i - 1]
            curr_meta = self.fixation_sequence[i]
            
            transitions.append((prev_meta["name"], curr_meta["name"]))
            
            # If current region starts before the previous one, it's a regression
            if curr_meta["start"] < prev_meta["start"]:
                regressions[curr_meta["name"]] += 1

        return region_seconds, self.region_fixations, regressions, transitions
