# cat-helpers

The three things [Local AI Cat](https://localaicat.com) asks your Mac's admin password for, published
so you can read exactly what runs as root before you say yes. These files are generated from the
app's own source and checked by its tests on every change: what is here is what the app runs.

| Helper | What it lets the Cat do | What it installs | How to remove it |
|---|---|---|---|
| [`locked-use/`](locked-use/) | Unlock your Mac for an agent you approved while you're away, and lock it again (AFK and Locked Use) | An authorization plug-in in `/Library/Security/SecurityAgentPlugins`, one rule in the authorization database, and a trust file holding the app's code hash | The Lock Screen screen in Utilities, or the AFK menu row's "Uninstall lock plug-in…", or run [`locked-use/uninstall.sh`](locked-use/uninstall.sh) as root |
| [`battery/`](battery/) | Switch Energy Mode (Low Power, Automatic, High Power) without asking each time | One sudoers rule allowing exactly five `pmset` commands, nothing else | `sudo rm /etc/sudoers.d/localaicat-battery` |
| [`screen-awake/`](screen-awake/) | Keep the Mac awake with the lid closed (Screen Awake) | One sudoers rule allowing exactly `pmset -a disablesleep 1` and `0` | `sudo rm /etc/sudoers.d/localaicat-screenawake` |

## Reading the Locked Use script

`install.sh` is the exact command list, one per line. Three values are filled in by the app on your
Mac; here they are examples:

- the path of the helper inside the app,
- `aaaa…`: the code hash of the Local AI Cat app that installed it (only that exact app may ask the
  helper to unlock),
- `bbbb…`: the code hash of the helper the app measured, which root checks again before installing.

The two long `base64` lines are [`authdb.py`](locked-use/authdb.py) (the one edit made to the
`system.login.screensaver` right) and [`rule.plist`](locked-use/rule.plist) (the rule it points at).
Every step is verified, and a failed verification puts the previous right back.

In the sudoers files, `you` stands for your macOS user name.

## Questions or problems

Open an issue in this repository.
