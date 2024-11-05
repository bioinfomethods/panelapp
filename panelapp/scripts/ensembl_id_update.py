#! /usr/bin/env python3
"""
Thin wrapper around "manage update_gene_ensembl /tmp/ensembl_id.json

Usage: ensembl_id_update PATH_or_S3_URL DIR_or_S3_URL_prefix
"""

import argparse
import contextlib
import os
import sys
import tempfile

import boto3
from django.core.management import execute_from_command_line


def parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input", help="Update JSON document, either a local path or a S3 URL"
    )
    parser.add_argument(
        "logs", help="Location of logs; either local dir or S3 URL prefix"
    )
    return parser.parse_args(argv)


@contextlib.contextmanager
def download(download_path: str):
    if download_path.startswith("s3://"):
        with tempfile.TemporaryDirectory() as tempdir:
            local_path = f"{tempdir}/ensembl_id_update.json"
            s3 = boto3.client("s3")
            bucket, _, key = download_path.removeprefix("s3://").partition("/")
            s3.download_file(bucket, key, local_path)
            yield local_path
    else:
        yield download_path


@contextlib.contextmanager
def upload(upload_path: str):
    if upload_path.startswith("s3://"):
        with tempfile.TemporaryDirectory() as tempdir:
            yield tempdir
            bucket, _, key_prefix = upload_path.removeprefix("s3://").partition("/")
            s3 = boto3.client("s3")
            for (dir_path, dirs, files) in os.walk(tempdir):
                for file_ in files:
                    local_file = f"{dir_path}/{file_}"
                    remote_file = (
                        f'{key_prefix}/{local_file.removeprefix(f"{tempdir}/")}'
                    )
                    s3.upload_file(local_file, bucket, remote_file)
    else:
        yield upload_path


@contextlib.contextmanager
def redirect(log_dir: str, stdout="stdout.log", stderr="stderr.log"):
    with open(f"{log_dir}/{stdout}", "w") as stdout_path:
        with contextlib.redirect_stdout(stdout_path):
            with open(f"{log_dir}/{stderr}", "w") as stderr_path:
                with contextlib.redirect_stderr(stderr_path):
                    yield


def main() -> None:
    args = parse(sys.argv[1:])
    with download(args.input) as local_input:
        with upload(args.logs) as local_output:
            with redirect(local_output, stdout="changes.log", stderr="errors.log"):
                execute_from_command_line(
                    ["manage", "update_gene_ensembl", local_input]
                )


if __name__ == "__main__":
    main()
