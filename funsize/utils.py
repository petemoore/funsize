import os
import requests
import redo
import logging
from taskcluster import encryptEnvVar

log = logging.getLogger(__name__)


def properties_to_dict(props):
    """Convert properties tuple into dict"""
    props_dict = {}
    for prop in props:
        if len(prop) >= 2:
            props_dict[prop[0]] = prop[1]
    return props_dict


def buildbot_to_treeherder(platform):
    # Coming from https://github.com/mozilla/treeherder/blob/master/ui/js/values.js
    m = {
        "linux": "linux32",
        "linux64": "linux64",
        "macosx64": "osx-10-10",
        "win32": "windowsxp",
        "win64": "windows8-64",
    }
    return m[platform]


def revision_to_revision_hash(th_api_root, branch, revision):
    url = "{th_api_root}/project/{branch}/resultset".format(
        th_api_root=th_api_root, branch=branch
    )
    # Use short revision for treeherder API
    revision = revision[:12]
    params = {"revision": revision}
    for _ in redo.retrier(sleeptime=5, max_sleeptime=30):
        params_str = "&".join("=".join([k, str(v)])
                              for k, v in params.iteritems())
        try:
            log.debug("Connecting to %s?%s", url, params_str)
            r = requests.get(url, params=params)
            return r.json()["results"][0]["revision_hash"]
        except:
            log.exception("Failed to connect to %s?%s", url, params_str)
    else:
        raise RuntimeError("Cannot fetch revision hash for {} {}".format(
            branch, revision))


def encryptEnvVar_wrapper(*args, **kwargs):
    """Wrap encryptEnvVar and pass key file path"""
    return encryptEnvVar(
        *args, keyFile=os.path.join(os.path.dirname(__file__),
                                    "data", "docker-worker-pub.pem"),
        **kwargs)
