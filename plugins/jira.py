#!/usr/bin/python3
# -*- coding: utf-8 -*-

# TODO:
# - Create an endpoint to get all issues assigned to a user
# - Create an endpoint to create new issues/story
# - Add ACL for endpoints
# - Should `sprint` endpoint show all issues or only opened ?
# - Assign issue to a user based on mattermost username translated to Jira
#   user based on his email
# - Add more info in issue details
# - Return one multi line message instead of several messages

import re
import os

from mattermost_bot.bot import respond_to
from jira import JIRA

JIRA_URL = os.environ.get("MATTERBOT_JIRA_URL")
PROJECT = os.environ.get("MATTERBOT_JIRA_PROJECT")
JIRA_CONNECTOR = JIRA(JIRA_URL, basic_auth=(
    os.environ.get("MATTERBOT_JIRA_LOGIN"),
    os.environ.get("MATTERBOT_JIRA_PASSWORD")
))

STATUSES_EMOJI = {
    "A faire": ":new:",
    "En cours": ":hammer_and_wrench:",
    "Needs Review": ":clock1:",
    "Fini": ":white_check_mark:",
    "Canceled": ":x:",
}


@respond_to('{} issues'.format(PROJECT), re.IGNORECASE)
def issues(message):
    """Print opened issues"""
    issues = JIRA_CONNECTOR.search_issues(
        """project={} and
        status != Done and
        status != Canceled and
        (type = Bogue or type = Story)
        order by priority desc
        """.format(PROJECT)
    )

    for issue in issues:
        msg = "[{0}]({1}/browse/{0}) - {2} {3}".format(
            issue.key,
            JIRA_URL,
            issue.fields.summary,
            STATUSES_EMOJI[issue.fields.status.name],
        )
        message.send(msg)


@respond_to('{} sprint'.format(PROJECT), re.IGNORECASE)
def active_sprint(message):
    """Print active sprint issues"""
    issues = JIRA_CONNECTOR.search_issues(
        """project={} and
        status != Done and
        status != Canceled and
        (type = Bogue or type = Story)
        and sprint in openSprints()
        order by status desc
        """.format(PROJECT)
    )

    for issue in issues:
        msg = "[{0}]({1}/browse/{0}) - {2} {3}".format(
            issue.key,
            JIRA_URL,
            issue.fields.summary,
            STATUSES_EMOJI[issue.fields.status.name],
        )
        message.send(msg)


@respond_to('{} issue (.*)'.format(PROJECT), re.IGNORECASE)
def get_issue(message, key=None):
    """Get issue detail from its key"""
    if key:
        issue = JIRA_CONNECTOR.issue(key)
        message.send("[{0}]({1}/browse/{0})".format(issue.key, JIRA_URL))
        message.send(issue.fields.summary)
        message.send("{} - {}".format(
            STATUSES_EMOJI[issue.fields.status.name],
            issue.fields.status.name
        ))
        if issue.fields.assignee:
            message.send(issue.fields.assignee.displayName)
        else:
            message.send('Not assigned')
    else:
        message.send('You need to specify a key')


@respond_to('{} assign (.*)'.format(PROJECT), re.IGNORECASE)
@respond_to('{} assign (.*) to (.*)'.format(PROJECT), re.IGNORECASE)
def assign_issue(message, key=None, user=None):
    """Assign issue to user by default me"""
    if key:
        issue = JIRA_CONNECTOR.issue(key)
        if not user:
            # get current user by his mail
            mail = message.get_user_mail()
            users = JIRA_CONNECTOR.search_assignable_users_for_projects(
                "", PROJECT)
            match = [u for u in users if u.emailAddress == mail]
            if match:
                user = match[0].name
            else:
                message.send('Can not retrieve user from mail')

        if user:
            JIRA_CONNECTOR.assign_issue(issue, user)
    else:
        message.send('You need to specify a key')
