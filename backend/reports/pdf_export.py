from ..reports.report_formatter import ReportFormatter

class PDFExport:
    @staticmethod
    def _encode_text(text: str) -> str:
        return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    @staticmethod
    def create_pdf_bytes(report: dict) -> bytes:
        body_text = ReportFormatter.format_text(report)
        escaped = PDFExport._encode_text(body_text)
        content_stream = f"BT /F1 10 Tf 40 760 Td ({escaped}) Tj ET"
        content = content_stream.encode("latin-1", errors="replace")

        objects = []
        objects.append(b"%PDF-1.4\n")
        objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        objects.append(b"2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n")
        objects.append(
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\nendobj\n"
        )
        stream_obj = b"4 0 obj\n<< /Length %d >>\nstream\n" % len(content)
        objects.append(stream_obj)
        objects.append(content)
        objects.append(b"\nendstream\nendobj\n")
        objects.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

        offset = 0
        xref_lines = [b"xref\n0 %d\n" % len(objects), b"0000000000 65535 f \n"]
        body = [objects[0]]
        offset += len(objects[0])

        for obj in objects[1:]:
            xref_lines.append(b"%010d 00000 n \n" % offset)
            body.append(obj)
            offset += len(obj)

        trailer = b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%EOF\n" % (
            len(objects),
            offset,
        )

        return b"".join(body + xref_lines + [trailer])
