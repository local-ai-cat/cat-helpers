#!/usr/bin/env python3
"""Locked Use: the one transform of the `system.login.screensaver` right.

Reads the right's plist on stdin (the output of
`security authorizationdb read system.login.screensaver`) and, for `install`
and `uninstall`, writes the transformed plist to stdout for
`security authorizationdb write system.login.screensaver`.

Shape it produces, and the only shape it accepts (Apple's stock right and the
shape ChatGPT's locked use already installs are both this):

    class = rule, k-of-n = 1, rule = [ <our rule id>, ...foreign..., use-login-window-ui ]

`k-of-n = 1` is the safety story: our evaluate-mechanisms rule runs first and a
Deny, a dead socket, or a timeout falls through to the stock password UI.

Invariants (each pinned by scripts/tests/test_locked_use_authdb.py):
- install is idempotent and puts our id FIRST without reordering foreign ids;
- every foreign id and every unrelated key survives both directions;
- `use-login-window-ui` is always reachable after install;
- uninstall removes ONLY our id and restores the stock single-rule shape when
  nothing foreign remains;
- any right that is not `class = rule` is refused (exit 2) rather than guessed
  at, because wrapping an unknown shape is how a person gets locked out.

This file is embedded verbatim in
Packages/FeatureLockedUse/Sources/LockedUseKit/LockedUseAuthorizationDatabase.swift;
a test asserts the two are byte-identical.
"""
import json
import plistlib
import sys

STOCK_FALLBACK = "use-login-window-ui"


def _rules(right):
    rule = right.get("rule")
    if rule is None:
        return []
    if isinstance(rule, str):
        return [rule]
    if isinstance(rule, list) and all(isinstance(item, str) for item in rule):
        return list(rule)
    raise SystemExit(2)


def _refuse_unless_rule_class(right):
    if right.get("class") != "rule":
        sys.stderr.write("locked_use_authdb: refusing to transform a right whose class is %r\n" % right.get("class"))
        raise SystemExit(2)


def install(right, rule_id):
    _refuse_unless_rule_class(right)
    rules = [item for item in _rules(right) if item != rule_id]
    if STOCK_FALLBACK not in rules:
        rules.append(STOCK_FALLBACK)
    rules.insert(0, rule_id)
    right["rule"] = rules
    right["k-of-n"] = 1
    return right


def uninstall(right, rule_id):
    _refuse_unless_rule_class(right)
    rules = [item for item in _rules(right) if item != rule_id]
    if not rules:
        rules = [STOCK_FALLBACK]
    right["rule"] = rules
    if len(rules) == 1:
        right.pop("k-of-n", None)
    else:
        right["k-of-n"] = 1
    return right


def verify(right, rule_id):
    rules = _rules(right)
    ok = (
        right.get("class") == "rule"
        and rules[:1] == [rule_id]
        and STOCK_FALLBACK in rules
        and (len(rules) == 1 or right.get("k-of-n") == 1)
    )
    return ok


def status(right, rule_id):
    rules = _rules(right)
    return {
        "class": right.get("class"),
        "k_of_n": right.get("k-of-n"),
        "rules": rules,
        "installed": rule_id in rules,
        "first": rules[:1] == [rule_id],
        "fallback_reachable": STOCK_FALLBACK in rules,
    }


def main(argv):
    if len(argv) != 3 or argv[1] not in {"install", "uninstall", "verify", "status"}:
        sys.stderr.write("usage: locked_use_authdb.py {install|uninstall|verify|status} RULE_ID < right.plist\n")
        return 64
    command, rule_id = argv[1], argv[2]
    right = plistlib.loads(sys.stdin.buffer.read())
    if not isinstance(right, dict):
        raise SystemExit(2)
    if command == "install":
        plistlib.dump(install(right, rule_id), sys.stdout.buffer, sort_keys=True)
        return 0
    if command == "uninstall":
        plistlib.dump(uninstall(right, rule_id), sys.stdout.buffer, sort_keys=True)
        return 0
    if command == "verify":
        return 0 if verify(right, rule_id) else 1
    sys.stdout.write(json.dumps(status(right, rule_id), sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
