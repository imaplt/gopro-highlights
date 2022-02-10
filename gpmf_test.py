import argparse
import datetime
import io
import json
import logging
import os
import struct
import sys
import parser

LOG = logging.getLogger(__name__)

def parse(f, file_size):
    node_list = []
    while True:
        if f.tell() >= file_size:
            break

        four_cc = f.read(4).decode("ASCII")
        gpmf_type = f.read(1).decode("ASCII")
        gpmf_size = int.from_bytes(f.read(1), byteorder="big", signed=False)
        gpmf_repeat = int.from_bytes(f.read(2), byteorder="big", signed=False)
        raw_data = io.BytesIO(f.read(gpmf_size * gpmf_repeat))

        read_len = 8 + gpmf_size * gpmf_repeat
        mod = read_len % 4
        if mod != 0:
            f.read(4 - mod)

        if gpmf_type == "\x00":
            gpmf_type = ""

        print(f"<{four_cc}> <{gpmf_type}> {gpmf_size} {gpmf_repeat}")
        LOG.debug(f"<{four_cc}> <{gpmf_type}> {gpmf_size} {gpmf_repeat}")

        node = {
            "four_cc": four_cc,
            "type": gpmf_type,
            "size": gpmf_size,
            "repeat": gpmf_repeat,
            "raw_data": raw_data,
        }

        if node["type"] == "":
            node["data"] = parse(node["raw_data"], gpmf_size * gpmf_repeat)
        elif node["type"] == "c":
            samples = []
            if node["size"] == 1:
                raw_bytes = node["raw_data"].read(node["repeat"]).partition(b"\0")[0]
                samples = [[raw_bytes.decode("latin1")]]
            else:
                for sample_i in range(node["repeat"]):
                    raw_bytes = node["raw_data"].read(node["size"]).partition(b"\0")[0]
                    samples.append(raw_bytes.decode("latin1"))
            node["data"] = samples

        else:
            samples = []
            for sample_i in range(node["repeat"]):
                raw_bytes = node["raw_data"].read(node["size"])
                if node["type"] == "b":
                    values_per_sample = int(node["size"] / 1)
                    samples.append(
                        struct.unpack(">" + ("b" * values_per_sample), raw_bytes)
                    )
                elif node["type"] == "B":
                    values_per_sample = int(node["size"] / 1)
                    samples.append(
                        struct.unpack(">" + ("B" * values_per_sample), raw_bytes)
                    )
                elif node["type"] == "s":
                    values_per_sample = int(node["size"] / 2)
                    samples.append(
                        struct.unpack(">" + ("h" * values_per_sample), raw_bytes)
                    )
                elif node["type"] == "S":
                    values_per_sample = int(node["size"] / 2)
                    samples.append(
                        struct.unpack(">" + ("H" * values_per_sample), raw_bytes)
                    )
                elif node["type"] == "L":
                    values_per_sample = int(node["size"] / 4)
                    samples.append(
                        struct.unpack(">" + ("I" * values_per_sample), raw_bytes)
                    )
                elif node["type"] == "l":
                    values_per_sample = int(node["size"] / 4)
                    samples.append(
                        struct.unpack(">" + ("i" * values_per_sample), raw_bytes)
                    )
                elif node["type"] == "f":
                    values_per_sample = int(node["size"] / 4)
                    samples.append(
                        struct.unpack(">" + ("f" * values_per_sample), raw_bytes)
                    )
                elif node["type"] == "U":
                    values_per_sample = int(node["size"] / 16)
                    samples.append(parse_date(raw_bytes.decode("latin1")))
                elif node["type"] == "?":
                    pass
                else:
                    raise NotImplementedError("%s is not implimented" % node["type"])
            node["data"] = samples
            LOG.debug(node["data"])

        del node["raw_data"]
        node_list.append(node)

    return node_list


def parse_date(date_string: str) -> datetime.datetime:
    return dateutil.parser.parse(
        "{}-{}-{}T{}:{}:{}Z".format(
            2000 + int(date_string[:2]),  # years
            int(date_string[2:4]),  # months
            int(date_string[4:6]),  # days
            int(date_string[6:8]),  # hours
            int(date_string[8:10]),  # minutes
            float(date_string[10:]),  # seconds
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Convert GoPro Metadata files.")
    parser.add_argument("input file", type=str, help="Input file name")
    parser.add_argument("-o", "--output",  help="Output to a JSON file.", action="store_true")
    parser.add_argument("-v", "--verbose", help="Increase output verbosity.", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    filename = getattr(args, "input file")

    file_size = os.stat(filename).st_size
    LOG.info(f"File size is {file_size} bytes.")

    with open(filename, "rb") as f:
        nodes = parse(f, file_size)

    if args.output:
        LOG.info(f"Writing to file {filename}.json")
        with open(filename + ".json", "w") as f:
            json.dump(nodes, f, default=str)
    else:
        print(json.dumps(nodes, default=str))


if __name__ == "__main__":
    main()