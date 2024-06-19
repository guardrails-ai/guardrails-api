"""
All guards defined here will be initialized, if and only if
the application is using in memory guards.

The application will use in memory guards if pg_host is left
undefined. Otherwise, a postgres instance will be started
and guards will be persisted into postgres. In that case,
these guards will not be initialized.
"""
# from guardrails_hub import AtomicFactuality  # noqa
from guardrails import Guard
import openai
# from guardrails import AsyncGuard  # noqa
# from langchain_community.embeddings.sentence_transformer import (
#     SentenceTransformerEmbeddings,
# )

# SOURCES = [
#     "Albert Einstein Albert Einstein ( ; ; 14 March 1879\u00a0\u2013 18 April 1955) was a German-born theoretical physicist, widely acknowledged to be one of the greatest and most influential physicists of all time.",
#     "Einstein is best known for developing the theory of relativity, but he also made important contributions to the development of the theory of quantum mechanics.",
#     "Relativity and quantum mechanics are the two pillars of modern physics.",
#     'His mass\u2013energy equivalence formula, which arises from relativity theory, has been dubbed "the world\'s most famous equation".',
#     "His work is also known for its influence on the philosophy of science.",
#     'He received the 1921 Nobel Prize in Physics "for his services to theoretical physics, and especially for his discovery of the law of the photoelectric effect", a pivotal step in the development of quantum theory.',
#     'His intellectual achievements and originality resulted in "Einstein" becoming synonymous with "genius".',
#     "Einsteinium, one of the synthetic elements in the periodic table, was named in his honor.",
#     "In 1905, a year sometimes described as his \"annus mirabilis\" ('miracle year'), Einstein published four groundbreaking papers.",
#     "These outlined the theory of the photoelectric effect, explained Brownian motion, introduced special relativity, and demonstrated mass\u2013energy equivalence.",
# ]

# embed_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# atomic_guard = AsyncGuard()
# atomic_guard.use(
#     AtomicFactuality,
#     sources=SOURCES,
#     embedding_callable=embed_function,
# )

no_guards = Guard()
no_guards.name = "No Guards"