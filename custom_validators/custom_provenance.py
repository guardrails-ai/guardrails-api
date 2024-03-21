from typing import Any, Dict, Callable
from functools import partial

from guardrails.validator_base import (
    register_validator,
)
from guardrails.hub import ProvenanceEmbeddings
from sentence_transformers import SentenceTransformer


@register_validator(name="custom/provenance", data_type="string")
class CustomProvenance(ProvenanceEmbeddings):
   def get_query_function(self, metadata: Dict[str, Any]) -> Callable:
        """Override to set our custom embedding function"""
        sources = metadata.get("sources")
        if not sources:
            raise ValueError(
                "You must provide `sources` in metadata."
            )

        MODEL = SentenceTransformer("paraphrase-MiniLM-L6-v2")
        
        return partial(
            ProvenanceEmbeddings.query_vector_collection,
            sources=metadata.get("sources", []),
            embed_function=MODEL.encode
        )