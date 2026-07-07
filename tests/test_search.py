from modric_cli import search


def test_collector_caps_total_at_1000():
    col = search.Collector(limit=5000)          # request above the hard cap
    assert col.limit == 1000
    for i in range(1005):
        col.add({"i": i})
    r = col.result()
    assert r["returned"] == 1000 and r["truncated"] is True


def test_snippet_clamped_to_10kb():
    col = search.Collector()
    col.add({"snippet": "x" * (20 * 1024)})
    snippet = col.result()["results"][0]["snippet"]
    assert len(snippet.encode("utf-8")) <= 10 * 1024 + 40      # +truncation note
    assert "truncated to 10 KB" in snippet


def test_grep_returns_context_window():
    text = "\n".join(f"line{i}" for i in range(10))
    blocks = search.grep(text, search.compile_query("line5"), before=1, after=2)
    assert len(blocks) == 1
    snippet = blocks[0]["snippet"]
    assert "5: line4" in snippet          # before
    assert "6: line5" in snippet          # the match
    assert "8: line7" in snippet          # after
    assert "line8" not in snippet         # nothing beyond the window
