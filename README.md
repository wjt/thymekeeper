Do not use this program.

## Now we've got that out of the way

If you track work done for your clients by putting events into a calendar, and
that calendar is accessible over CalDAV, this program can summarize it for you.

## `thymekeeper.ini`

```ini
[DEFAULT]
# or however you get your passwords out of your password safe
# %(username)s is interpolated by Python's ini file parser
# so you can put whatever key you need to into each account
password-command=vault '%(username)s'

[client-name-here]
url=https://my.wonderful/caldav/url
username=mallory

[another-client-name-here]
url=...
username=mallory
# or you can just specify the password command separately per account
password-command=echo -n topsecret
```

