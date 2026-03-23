from guardrails import Guard
from guardrails.hub import TwoWords

# instantiate guards
guard0 = Guard(id="test-guard", name="test-guard").use(TwoWords(on_fail="fix"))
