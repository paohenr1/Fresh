"""Local interactive FRESH planner. Run `python app.py`, then open its address."""

import argparse
import csv
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
import json
from pathlib import Path

from inputs import scenario_from_dict
from projection import project
from reporting import annual_table, render_html, summary

ROOT = Path(__file__).parent


def calculate(data: dict) -> dict:
    """Use the same validated Python engine for the screen and both downloads."""
    scenario = scenario_from_dict(data)
    as_of = date.fromisoformat(data['as_of'])
    projection = project(scenario, as_of)
    records = annual_table(projection, scenario)
    payload = {'as_of': data['as_of'], 'inputs': data,
               'summary': summary(projection, scenario), 'annual_table': records}
    stream = StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
    return {'html': render_html(projection, scenario), 'projection': payload,
            'csv': stream.getvalue()}


def create_server(data: dict, port: int = 8765) -> ThreadingHTTPServer:
    """Bind only to this computer; each request supplies its own unsaved scenario."""
    scenario = scenario_from_dict(data)
    projection = project(scenario, date.fromisoformat(data['as_of']))
    initial_html = render_html(projection, scenario, live_inputs=data)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            # Avoid logging financial input values or request bodies.
            pass

        def respond(self, status: int, content: str | bytes, content_type: str,
                    filename: str | None = None) -> None:
            body = content.encode('utf-8') if isinstance(content, str) else content
            self.send_response(status)
            self.send_header('Content-Type', content_type + ('; charset=utf-8' if isinstance(content, str) else ''))
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            if filename:
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path in ('/', '/report.html'):
                self.respond(200, initial_html, 'text/html')
            else:
                self.respond(404, 'Not found', 'text/plain')

        def do_POST(self) -> None:
            if self.path not in ('/api/project', '/api/pdf/client', '/api/pdf/advisor'):
                self.respond(404, 'Not found', 'text/plain')
                return
            # Only same-origin JSON requests may call the local calculator.
            origin = self.headers.get('Origin')
            allowed = {f'http://127.0.0.1:{self.server.server_port}',
                       f'http://localhost:{self.server.server_port}'}
            if (origin is not None and origin not in allowed) or self.headers.get_content_type() != 'application/json':
                self.respond(403, json.dumps({'error': 'Use the local planner page.'}), 'application/json')
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 100_000:
                    raise ValueError('Invalid request size')
                inputs = json.loads(self.rfile.read(length))
                if not isinstance(inputs, dict):
                    raise ValueError('Expected scenario inputs')
                if self.path.startswith('/api/pdf/'):
                    # Recalculate the submitted scenario, not startup data or a saved file.
                    from pdf_reporting import export_pdf
                    kind = self.path.rsplit('/', 1)[-1]
                    timestamp = datetime.now(timezone.utc)
                    basis = self.headers.get('X-FRESH-Dollar-Basis', 'nominal_cad')
                    content = export_pdf(inputs, kind, timestamp, basis=basis)
                    self.respond(200, content, 'application/pdf', f'fresh-{kind}-{timestamp:%Y-%m-%d}.pdf')
                else:
                    result = calculate(inputs)
                    self.respond(200, json.dumps(result, allow_nan=False), 'application/json')
            except ImportError:
                self.respond(503, json.dumps({'error': 'PDF support is missing. Install requirements.txt and restart the planner.'}), 'application/json')
            except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as error:
                self.respond(400, json.dumps({'error': str(error)}), 'application/json')

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', nargs='?', type=Path, default=ROOT / 'examples/fictional.json')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    try:
        data = json.loads(args.inputs.read_text(encoding='utf-8'))
        # A downloaded projection includes its effective input record.
        if isinstance(data, dict) and 'inputs' in data:
            data = data['inputs']
        server = create_server(data, args.port)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(2, f'FRESH: {error}\n')
    print(f'FRESH planner: http://127.0.0.1:{server.server_port}', flush=True)
    print('Keep this terminal open. Press Ctrl+C to stop. Export an advisor PDF to keep a record of your inputs and results.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
