# Decisions

## 1. Where the AI got it wrong
(Numbers like `[0230]` are entry numbers in `session-log.md`.)

**It never limited how long a sample size could be.** The AI's first `app.py` `[0101]` turned the text into a number with a bare `return int(text)`. Python refuses strings over 4,300 digits, so a long number put Python's own error on the page. The AI's tests only tried `0`, `-1`, `abc`, `12.5` and an empty box. I found it by trying the site, and told the AI at `[0230]`: *"There is another problem right now that when i enter a number above 4300 digits in the sample size input field, I see this error."* The AI reproduced it at `[0237]`: *"Exceeds the limit (4300 digits) for integer string conversion: value has 10353 digits"*. The same output shows a 4,300-digit number was silently accepted (*"4300 digits -> 302 no error shown"*). The AI's own summary at `[0261]`: *"I should have checked the length first."* The fix `[0242]` caps the size at 1,000,000 and adds tests.

**Its first tests would not catch a mistyped table.** They only checked where each row starts. The AI raised this itself at `[0212]`: *"My tests only check which row starts where. A typo in, say, the 600 row's limits (12 and 26) would not be caught."* I asked it to explain `[0213]`. It changed the 600 row to `(600, 21, 62)` in a scratch copy, and all 31 tests still passed `[0215]`: *"600 sample, 13 major (should be REJECT, limit is 12): ACCEPT"*. The tests that check every limit were added at `[0221]`.

## 2. What I chose not to build, and why
Everything the brief ruled out (login, database, styling, deployment, multi-user, edit/delete). Also no CLI: the AI suggested one as quicker, but I chose a website because it is closer to what an inspector would use. No double-submit protection, undo, file locking, or batch history, since each would need features the brief puts out of scope.

## 3. What was ambiguous
- **Same batch ID started again:** I assumed one current inspection, so starting again silently overwrites it, even with the same batch ID and a different sample size.
- **Identical defects:** each record counts as one defect, because different units can share a defect and every one counts toward the limits.
- **Placeholder descriptions** such as `-` or `.` pass; only empty text is refused.
- **Sample size:** the brief sets no maximum, so I chose 1,000,000. Sizes above 600 use the 600 row.
- **The six expected cases:** I traced them by hand and none disagrees with my reading.

## 4. Three things that could still go wrong that the tests don't cover
1. **Double-click on "Record defect"** records two identical defects. The app can't tell them from two real ones, and there is no undo, so one extra defect can flip ACCEPT to REJECT.
2. **Two requests at the same moment:** the JSON file is read, changed and rewritten with no locking, so one defect could be lost.
3. **A damaged `inspection.json`** (half-written or edited by hand) makes every page return a server error. Deleting the file fixes it.
