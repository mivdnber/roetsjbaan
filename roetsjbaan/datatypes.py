import collections

class SliceableDict(collections.OrderedDict):
    def __getitem__(self, key):
        stop_offset = 0

        if isinstance(key, tuple):
            key, stop_offset = key

        if isinstance(key, slice):
            return self.values()[self.__calculate_slice(key, stop_offset)]

        return super(SliceableDict, self).__getitem__(key)

    def __calculate_slice(self, key, stop_offset=0):
        start, stop, step = key.start, key.stop, key.step

        if start:
            start = next(
                i for i, (k, v) in enumerate(self.items())
                if k == start
            )

        if stop:
            stop = next(
                i for i, (k, v) in enumerate(self.items())
                if k == stop
            ) + stop_offset


        return slice(start, stop, step)
