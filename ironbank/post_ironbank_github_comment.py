#!/usr/bin/env python

import argparse
import requests
import subprocess
import os
import re


def post_comment(image_names):
    if not os.environ.get('GITHUB_KEY'):
        print("No github key set. Will not post a message!")
        return
    if os.environ.get('CIRCLE_PULL_REQUEST'):
        # change: https://github.com/demisto/dockerfiles/pull/9
        # to: https://api.github.com/repos/demisto/dockerfiles/issues/9/comments
        post_url = os.environ['CIRCLE_PULL_REQUEST'].replace('github.com', 'api.github.com/repos').replace('pull', 'issues') + "/comments"
    else:
        # try to get from comment
        last_comment = subprocess.check_output(["git", "log", "-1", "--pretty=%B"])
        m = re.search(r"#(\d+)", last_comment, re.MULTILINE)
        if not m:
            print("No issue id found in last commit comment. Ignoring: \n------\n{}\n-------".format(last_comment))
            return
        issue_id = m.group(1)
        print("Issue id found from last commit comment: " + issue_id)
        post_url = "https://api.github.com/repos/demisto/dockerfiles/issues/{}/comments".format(issue_id)

    message = f"# Ironbank Generated Images"
    commit = os.environ.get('CIRCLE_SHA1')
    if commit:
        message += f" - Commit: {commit}"
    message += "\n\n"
    for image_name in image_names:
        url = f"https://repo1.dso.mil/dsop/opensource/palo-alto-networks/demisto/{image_name}/-/pipelines"
        message += f"- {image_name}: [{url}]({url})\n"
    print("Going to post comment:\n\n{}".format(message))
    res = requests.post(post_url, json={"body": message}, auth=(os.environ['GITHUB_KEY'], 'x-oauth-basic'))
    try:
        res.raise_for_status()
    except Exception as ex:
        print("Failed comment post: {}".format(ex))


def args_handler():
    desc = """Post a message to github about the created image. Relies on environment variables:
    GITHUB_KEY: api key of user to use for posting
    CIRCLE_PULL_REQUEST: pull request url to use to get the pull id. Such as: https://github.com/demisto/dockerfiles/pull/9
    if CIRCLE_PULL_REQUEST will try to get issue id from last commit comment"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--docker_image_dirs', help='The path to the docker image dirs in the dockerfiles project',
                        required=True)
    return parser.parse_args()


def main():
    args = args_handler()
    docker_image_dirs = args.docker_image_dirs
    post_comment([os.path.basename(docker_image_dir) for docker_image_dir in docker_image_dirs.split(',')])


if __name__ == "__main__":
    main()