'''
All guards defined here will be initialized, if and only if
the application is using in memory guards.

The application will use in memory guards if pg_host is left
undefined. Otherwise, a postgres instance will be started 
and guards will be persisted into postgres. In that case,
these guards will not be initialized.
'''

from guardrails import Guard
from guardrails.hub import RegexMatch, ValidChoices, ValidLength #, RestrictToTopic

name_case = Guard(
    name='name-case',
    description='Checks that a string is in Name Case format.'
).use(
    RegexMatch(regex="^(?:[A-Z][^\s]*\s?)+$")
)

all_caps = Guard(
    name='all-caps',
    description='Checks that a string is all capital.'
).use(
    RegexMatch(regex="^[A-Z\\s]*$")
)

lower_case = Guard(
    name='lower-case',
    description='Checks that a string is all lowercase.'
).use(
    RegexMatch(regex="^[a-z\\s]*$")
).use(
    ValidLength(1, 100)
).use(
    ValidChoices(["music", "cooking", "camping", "outdoors"])
)

print(lower_case.to_json())




# valid_topics = ["music", "cooking", "camping", "outdoors"]
# invalid_topics = ["sports", "work", "ai"]
# all_topics = [*valid_topics, *invalid_topics]

# def custom_llm (text: str, *args, **kwargs):
#     return [
#         {
#             "name": t,
#             "present": (t in text),
#             "confidence": 5
#         }
#         for t in all_topics
#     ]
    
# custom_code_guard = Guard(
#     name='custom',
#     description='Uses a custom llm for RestrictToTopic'
# ).use(
#     RestrictToTopic(
#         valid_topics=valid_topics,
#         invalid_topics=invalid_topics,
#         llm_callable=custom_llm,
#         disable_classifier=True,
#         disable_llm=False,
#         # Pass this so it doesn't load the bart model
#         classifier_api_endpoint="https://m-1e7af27102f54c3a9eb9cb11aa4715bd-m.default.model-v2.inferless.com/v2/models/RestrictToTopic_1e7af27102f54c3a9eb9cb11aa4715bd/versions/1/infer",
#     )
# )