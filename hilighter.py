from dataclasses import dataclass
from datetime import timedelta
import struct

@dataclass
class Atom:
    name: str
    size: int

def yield_box(stream):
    while 1:
        size = stream.read(4)
        if len(size) < 4 : break
        n = int(struct.unpack('>I', size)[0])
        name = stream.read(4)
        yield Atom(name, n-8)

def move_stream_to(stream, n):
    chunks = 64 * (1 << 20)
    while n > chunks:
        stream.seek(chunks, 1)
        n -= chunks
    stream.seek(n, 1)

def find_hilights(filename):
    with open(filename, 'rb') as f:
        for atom in yield_box(f):
            if atom.name == b'moov':
                for atom in yield_box(f):
                    if atom.name == b'udta':
                        for atom in yield_box(f):
                            if atom.name == b'HMMT':
                                nb_hilights = int.from_bytes(f.read(4), byteorder='big')
                                if nb_hilights:
                                    return struct.unpack('>' + 'i' * nb_hilights, f.read(4 * nb_hilights))
                                else:
                                    return ()
                            else:
                                move_stream_to(f, atom.size)
                    else:
                        move_stream_to(f, atom.size)
            else:
                move_stream_to(f, atom.size)
    return ()


def print_time(time_ms):
    t = timedelta(milliseconds=time_ms)
    print(t)

if __name__ == '__main__':
    file = "/Users/imaplt/PycharmProjects/GoProVideos/GS010013.360"
    for t in find_hilights(file):
        print_time(t)