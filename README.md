# notfollowingback

A tiny terminal tool that finds the Instagram accounts **you follow that don't
follow you back**.

It supports two ways of getting your follower/following lists. Use whichever
suits you — there are **no dependencies to install for the recommended mode**.

| Mode | Accuracy | Risk to your account | Setup |
|------|----------|----------------------|-------|
| `export` (recommended) | Exact | None | Request a data download from Instagram |
| `login` | Exact | Instagram may rate-limit/flag automated logins | `pip install instaloader` |

> Instagram has no official API that returns follower/following lists for
> personal accounts, so these are the two realistic options. The `export` mode
> is recommended because it is fully within Instagram's Terms and cannot get
> your account flagged.

Requires **Python 3.7+**. No installation needed for `export` mode.

---

## Mode 1: `export` — official data download (recommended)

### Step 1 — Request your data from Instagram
1. Open Instagram → **Settings → Accounts Center → Your information and
   permissions → Download your information**.
   (Or go to <https://accountscenter.instagram.com/info_and_permissions/>.)
2. Choose **Download or transfer information** → select your account.
3. Select **Some of your information**, then under **Connections** tick
   **Followers and following**.
4. For **format**, choose **JSON** (⚠️ important — not HTML).
   Date range: **All time**.
5. Submit. Instagram emails you a download link, usually within minutes to a
   few hours.

### Step 2 — Run the tool
Point `--path` at the ZIP you downloaded (no need to unzip):

```bash
python3 notfollowingback.py export --path ~/Downloads/instagram-yourname.zip
```

It also accepts an already-extracted folder or a single JSON file:

```bash
python3 notfollowingback.py export --path ~/Downloads/instagram-yourname/
```

---

## Mode 2: `login` — live fetch (optional)

This logs in as you and pulls the lists directly. Convenient, but Instagram
actively discourages automated access and may throttle or temporarily challenge
your account, especially for accounts with many followers. Use sparingly.

### Setup
```bash
pip install -r requirements.txt   # installs instaloader
```

### Run
```bash
python3 notfollowingback.py login --username yourname
```

You'll be prompted for your password securely (it is never shown or stored as
plain text). Two-factor auth is supported. A login session is cached locally
(`session-yourname`) so subsequent runs don't need to log in again. That session
file holds auth cookies — it's git-ignored; don't share it.

---

## Example output

```
  Following:            312
  Followers:            289
  Don't follow back:    47

  Accounts you follow that do NOT follow you back:
  ------------------------------------------------
  someaccount
      https://www.instagram.com/someaccount/
  another_one
      https://www.instagram.com/another_one/
  ...
```

## How it works

Both modes produce two sets of usernames — who you **follow** and who **follows
you** — then prints `following − followers`. Usernames are compared
case-insensitively. That's the whole thing; see
[`notfollowingback.py`](notfollowingback.py).
