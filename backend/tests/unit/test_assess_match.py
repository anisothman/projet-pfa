"""Garde-fou : on refuse l'analyse quand SerpAPI n'a pas trouvé l'entreprise.

Sans cette vérification, le LLM hallucine un rapport (un prénom -> une boîte fictive).
"""

from localis.services.diagnostic import _assess_match
from localis.services.serp import SerpResult


def _serp(**kwargs) -> SerpResult:
    defaults = {
        "company_name": "test",
        "organic_results": [],
        "knowledge_graph": {},
        "related_searches": [],
        "raw": {},
    }
    defaults.update(kwargs)
    return SerpResult(**defaults)


def test_rich_knowledge_graph_passes():
    serp = _serp(
        knowledge_graph={"title": "KFC Tunis", "address": "Tunis", "phone": "+216...", "rating": 4.1},
    )
    status, _ = _assess_match(serp, "KFC")
    assert status == "ok"


def test_official_domain_match_passes():
    # Domaine reprend le nom → site officiel présumé.
    results = [
        {"title": "Samsung Official", "snippet": "Tech", "link": "https://www.samsung.com/global"},
        {"title": "Random article", "snippet": "Samsung mentioned", "link": "https://news.site/"},
    ]
    serp = _serp(organic_results=results)
    status, _ = _assess_match(serp, "Samsung")
    assert status == "ok"


def test_five_plus_mentions_pass():
    results = [
        {"title": f"Brand article {i}", "snippet": "Brand X review", "link": f"https://blog{i}.com/brandx"}
        for i in range(5)
    ]
    serp = _serp(organic_results=results)
    status, _ = _assess_match(serp, "Brand X")
    assert status == "ok"


def test_four_mentions_with_social_pass():
    results = [
        {"title": "Café X à Sousse", "snippet": "Café X", "link": "https://facebook.com/cafex"},
        {"title": "Photos Café X", "snippet": "Top café", "link": "https://instagram.com/cafex"},
        {"title": "Avis Café X", "snippet": "Client content", "link": "https://tripadvisor.com/cafex"},
        {"title": "Café X menu", "snippet": "Prices", "link": "https://blog.tn/cafex"},
    ]
    serp = _serp(organic_results=results)
    status, _ = _assess_match(serp, "Café X")
    assert status == "ok"


def test_first_name_without_business_signal_is_rejected():
    results = [
        {"title": "Wadi (prénom)", "snippet": "origine arabe", "link": "https://dictionary.com"},
        {"title": "Wadi Rum", "snippet": "désert jordanien", "link": "https://wiki.org"},
    ]
    serp = _serp(organic_results=results)
    status, reason = _assess_match(serp, "wadi")
    assert status == "insufficient"
    assert reason


def test_only_three_mentions_without_social_is_rejected():
    # 3 mentions seules ne suffisent plus — il faut 4 + plateforme métier, ou 5+.
    results = [
        {"title": "Foo blog 1", "snippet": "Foo discussed", "link": "https://blog.example.com/1"},
        {"title": "Foo blog 2", "snippet": "Foo reviewed", "link": "https://blog.example.com/2"},
        {"title": "Foo blog 3", "snippet": "Foo mentioned", "link": "https://blog.example.com/3"},
    ]
    serp = _serp(organic_results=results)
    status, _ = _assess_match(serp, "Foo")
    assert status == "insufficient"


def test_empty_results_rejected():
    serp = _serp(organic_results=[], knowledge_graph={})
    status, _ = _assess_match(serp, "anything")
    assert status == "insufficient"


def test_empty_query_rejected():
    serp = _serp(organic_results=[{"title": "x", "snippet": "y", "link": "z"}])
    status, _ = _assess_match(serp, "   ")
    assert status == "insufficient"
