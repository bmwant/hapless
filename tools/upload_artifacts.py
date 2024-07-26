"""
Script to upload release artifacts to Github Releases assets.
"""

import argparse
import logging
import os
from pathlib import Path

from github3 import GitHub
from github3.exceptions import NotFoundError

GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "bmwant")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "hapless")


def upload_to_github_releases(tag_name: str, artifact_path: Path, token: str):
    gh = GitHub(token=token)
    repo = gh.repository(owner=GITHUB_OWNER, repository=GITHUB_REPO)
    try:
        release = repo.release_from_tag(tag_name)
        logging.info(f"Fetched release: {release} with tag name : {tag_name}")
        logging.info(f"Attaching artifact {artifact_path.name} to release : {tag_name}")
        with open(artifact_path, "rb") as f:
            release.upload_asset(
                content_type="application/binary", name=artifact_path.name, asset=f
            )
    except (Exception, NotFoundError) as e:
        logging.error(f"Error while attaching artifact for the tag : {tag_name}")
        raise e


def upload_release_artifact(github_token, tag_name, artifact_file_path):
    artifact_path = Path(artifact_file_path)
    upload_to_github_releases(
        tag_name=tag_name, artifact_path=artifact_path, token=github_token
    )


if __name__ == "__main__":
    """
    Usage:
    python tools/upload_artifacts.py \
        --github-token <GITHUB_ACCESS_TOKEN> \
        --tag 'v0.1.9' \
        --artifact 'dist/hapless-0.1.9-py3-none-any.whl'
    """
    logging.basicConfig(level="INFO", format="%(message)s")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-gt",
        "--github-token",
        required=True,
        help="oauth token for github",
    )
    parser.add_argument(
        "-t",
        "--tag",
        required=True,
        help="release tag name for which atrifact would be uploaded",
    )
    parser.add_argument(
        "-f",
        "--artifact",
        required=True,
        help="file path to the artifact",
    )
    args = parser.parse_args()

    upload_release_artifact(
        github_token=args.github_token,
        tag_name=args.tag,
        artifact_file_path=args.artifact,
    )
