from localis.services.diagnostic import ReportStore


def test_save_and_load_roundtrip(tmp_path, sample_report):
    store = ReportStore(reports_dir=tmp_path)
    store.save(sample_report)

    loaded = store.load(sample_report.id)

    assert loaded is not None
    assert loaded.entreprise.nom == "Acme Corp"
    assert len(loaded.diagnostic.points_forts) == 1


def test_missing_report_returns_none(tmp_path):
    store = ReportStore(reports_dir=tmp_path)
    assert store.load("nope") is None
