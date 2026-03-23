from guardrails import Guard
from guardrails.hub import TwoWords

# instantiate guards
guard0 = Guard(name="test-guard").use(TwoWords(on_fail="fix"))
