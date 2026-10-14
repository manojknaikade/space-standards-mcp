import docx

from spacestd.loaders import load_document


def test_docx_loader_with_filename_meta(tmp_path):
    path = tmp_path / "DEMO-E-ST-97C_Rev.1.docx"
    d = docx.Document()
    for line in [
        "4 Requirements",
        "4.1 Interfaces",
        "a. The supplier shall document every external interface.",
        "NOTE Invented text for testing.",
    ]:
        d.add_paragraph(line)
    d.save(path)

    doc = load_document(path)
    assert (doc.doc_id, doc.issue) == ("DEMO-E-ST-97C", "Rev.1")
    [req] = doc.requirements
    assert req.req_id == "4.1a"
    assert req.notes == ["Invented text for testing."]
