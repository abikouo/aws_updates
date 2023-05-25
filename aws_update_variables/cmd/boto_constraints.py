#!/usr/bin/env python3
"""Script to update boto* library constraints aws hard-coded variable."""

import logging
import re

from pathlib import PosixPath
from argparse import ArgumentParser


FORMAT = "[%(asctime)s] - %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)


def main() -> None:
    """Read boto constraints and update variables accordingly."""
    parser = ArgumentParser()
    parser.add_argument(
        "-p", "--path", help="The path to the collection", required=True, type=PosixPath
    )
    args = parser.parse_args()

    # Read boto constraints
    requirements = PosixPath(args.path / "requirements.txt")
    constraints = {}
    if requirements.exists():
        for line in requirements.read_text().splitlines():
            if m := re.match(r"^(boto3|botocore)([>=<0-9\.]+)$", line.replace(" ", "")):
                constraints[m.group(1)] = m.group(2)
    logger.info("Requirements => %s", constraints)

    # Update test constraints
    for txtfile in ("tests/unit/constraints.txt", "tests/integration/constraints.txt"):
        p_file = PosixPath(args.path / txtfile)
        if p_file.exists():
            data = p_file.read_text()
            for key, value in constraints.items():
                data = re.sub(
                    rf"^{key}==([0-9\.]+)$",
                    key + "==" + re.search("[0-9\.]+", value).group(0),
                    data,
                    flags=re.MULTILINE,
                )
            if data != p_file.read_text():
                logger.info("updating file -> %s", txtfile)
                p_file.write_text(data)

    # Update MINIMUM_(BOTO3|BOTOCORE)_VERSION hard-coded variables
    for pyfile in PosixPath(args.path / "plugins").glob("*.py"):
        data = pyfile.read_text()
        for key, value in constraints.items():
            start_key = f"MINIMUM_{key.upper()}_VERSION = "
            min_version = re.search("[0-9\.]+", value).group(0)
            new_content = []
            for line in data.split("\n"):
                u = line
                if line.startswith(start_key):
                    m = re.match(rf"^{start_key}(['|\"])([0-9\.]+)(['|\"])(.*)", line)
                    if m:
                        u = start_key + m.group(1) + min_version + m.group(3) + m.group(4)
                new_content.append(u)
            data = "\n".join(new_content)
        if data != pyfile.read_text():
            logger.info("updating file -> %s", pyfile)
            pyfile.write_text(data)


if __name__ == "__main__":
    main()
