#!/usr/bin/env python3
"""
notfollowingback — find Instagram accounts you follow that don't follow you back.

Two modes:

  export   Parse Instagram's official "Download Your Information" data
           (recommended: accurate, safe, no risk to your account).

  login    Log in live with instaloader and fetch the lists directly
           (convenient, but Instagram rate-limits/flags automated logins).

Run `python3 notfollowingback.py --help` for details.
"""

import argparse
import json
import os
import sys
import zipfile


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #

def _username_from_href(href):
    """Pull the username out of a profile URL.

    Instagram uses two shapes:
        https://www.instagram.com/<username>
        https://www.instagram.com/_u/<username>   (seen in 'following')
    """
    if not href:
        return None
    slug = href.rstrip("/").split("/")[-1]
    return slug or None


def _usernames_from_string_list(entries):
    """Yield usernames from Instagram's nested 'string_list_data' structure.

    The username lives in different places depending on which file this is:
    followers use string_list_data[].value, while following uses the entry's
    'title' (with no value) and a /_u/ href. Try each in turn.
    """
    for entry in entries:
        name = None
        for item in entry.get("string_list_data", []):
            name = item.get("value") or _username_from_href(item.get("href"))
            if name:
                break
        if not name:
            name = entry.get("title")
        if name:
            yield name.strip().lower()


def report(following, followers):
    """Print the set of accounts you follow that don't follow you back."""
    not_following_back = sorted(following - followers)

    print()
    print(f"  Following:            {len(following)}")
    print(f"  Followers:            {len(followers)}")
    print(f"  Don't follow back:    {len(not_following_back)}")
    print()

    if not not_following_back:
        print("  Everyone you follow follows you back. ")
        return

    print("  Accounts you follow that do NOT follow you back:")
    print("  " + "-" * 48)
    for name in not_following_back:
        print(f"  {name}")
        print(f"      https://www.instagram.com/{name}/")
    print()


# --------------------------------------------------------------------------- #
# Mode: export  (parse the official data download)
# --------------------------------------------------------------------------- #

def _load_json_bytes(raw):
    return json.loads(raw.decode("utf-8"))


def _extract_followers(data):
    """followers files are usually a bare list; sometimes wrapped in a dict."""
    if isinstance(data, dict):
        for key in data:
            if key.startswith("relationships_follow"):
                data = data[key]
                break
    return set(_usernames_from_string_list(data)) if isinstance(data, list) else set()


def _extract_following(data):
    """following.json wraps the list under 'relationships_following'."""
    if isinstance(data, dict):
        data = data.get("relationships_following", [])
    return set(_usernames_from_string_list(data)) if isinstance(data, list) else set()


def _iter_files(path):
    """Yield (filename, raw_bytes) from a ZIP, a directory, or a single file."""
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.endswith(".json"):
                    yield name, zf.read(name)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for fn in files:
                if fn.endswith(".json"):
                    full = os.path.join(root, fn)
                    with open(full, "rb") as fh:
                        yield full, fh.read()
    else:
        with open(path, "rb") as fh:
            yield path, fh.read()


def run_export(path):
    followers, following = set(), set()
    found_following = False

    for name, raw in _iter_files(path):
        base = os.path.basename(name).lower()
        try:
            data = _load_json_bytes(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        if base.startswith("follower"):
            followers |= _extract_followers(data)
        elif base.startswith("following"):
            following |= _extract_following(data)
            found_following = True

    if not following and not found_following:
        sys.exit(
            "Couldn't find a 'following' file in that path.\n"
            "Point --path at your Instagram data export ZIP, its extracted\n"
            "folder, or the connections/followers_and_following directory.\n"
            "Make sure you requested the data in JSON format (not HTML)."
        )

    report(following, followers)


# --------------------------------------------------------------------------- #
# Mode: login  (live fetch via instaloader)
# --------------------------------------------------------------------------- #

def run_login(username, password):
    try:
        import instaloader
    except ImportError:
        sys.exit(
            "instaloader is not installed. Install it with:\n"
            "    pip install instaloader\n"
            "or just use the safer 'export' mode instead."
        )

    import getpass

    L = instaloader.Instaloader(quiet=True)

    if not username:
        username = input("Instagram username: ").strip()

    # Reuse a saved session if one exists; otherwise log in and save it.
    try:
        L.load_session_from_file(username)
        print(f"Loaded saved session for {username}.")
    except FileNotFoundError:
        if not password:
            password = getpass.getpass("Instagram password (hidden): ")
        try:
            L.login(username, password)
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            code = input("Two-factor code: ").strip()
            L.two_factor_login(code)
        L.save_session_to_file()

    print("Fetching profile…")
    profile = instaloader.Profile.from_username(L.context, username)

    print("Fetching following (this can take a while for large accounts)…")
    following = {p.username.lower() for p in profile.get_followees()}

    print("Fetching followers…")
    followers = {p.username.lower() for p in profile.get_followers()}

    report(following, followers)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Find Instagram accounts you follow that don't follow you back.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p_export = sub.add_parser(
        "export", help="Parse your official Instagram data download (recommended).")
    p_export.add_argument(
        "--path", required=True,
        help="Path to the export ZIP, its extracted folder, or a *.json file.")

    p_login = sub.add_parser(
        "login", help="Log in live via instaloader and fetch lists directly.")
    p_login.add_argument("--username", help="Your Instagram username.")
    p_login.add_argument(
        "--password",
        help="Your password (omit to be prompted securely; preferred).")

    args = parser.parse_args()

    if args.mode == "export":
        run_export(args.path)
    elif args.mode == "login":
        run_login(args.username, args.password)


if __name__ == "__main__":
    main()
