# Product roadmap

Window Swap should remain a small, local Windows utility. New features must preserve
the fast spatial gesture, require no account or administrator rights, and avoid
collecting window titles or contents.

## Next validation gate

Before adding more behavior, use `1.2.0-beta.2` daily on the current machine and on
at least one second Windows 11 system. Validate mixed DPI, monitors left/above the
primary display, Explorer, browsers, Store applications, and full-screen software.

## Strong candidates

1. **Choose the trigger corner per user.** Keep bottom-right as the default and add
   the other three corners for taskbars or applications that occupy that area.
2. **Optional keyboard cycle shortcut.** Provide an opt-in, conflict-detecting
   shortcut as an alternative to the pointer gesture; never capture arbitrary keys.
3. **Per-monitor trigger preferences.** Allow a trigger to be disabled on a display
   where the corner is frequently used for another control.
4. **Language selector.** Keep automatic English/Portuguese detection but allow an
   explicit choice in settings.
5. **Signed installer and clean upgrades.** Add code signing and a small installer
   only when a signing identity and sustainable release process exist.

## Deliberately deferred

- Automatic updates would add a network and supply-chain surface; keep releases
  manual unless the product explicitly adopts that responsibility.
- Rules based on window titles or captured contents conflict with the current
  privacy boundary.
- Automatic swapping without a click is likely to create accidental focus changes
  and should not be added without strong daily-use evidence.
