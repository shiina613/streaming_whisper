# HTTP API Server để lưu tài liệu cuộc họp
# Chạy song song với websocket_server.py
# Port: 8766

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from save_meeting_document import save_meeting_documents


class DocumentAPIHandler(BaseHTTPRequestHandler):
    
    def _send_cors_headers(self):
        """Gửi CORS headers để cho phép request từ browser"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def _send_json_response(self, data, status=200):
        """Gửi JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle preflight CORS request"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        """Handle POST request"""
        if self.path == '/save-document':
            try:
                # Đọc body
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))
                
                meeting_info = data.get('meetingInfo', {})
                content = data.get('content', '')
                
                if not meeting_info.get('meetingCode'):
                    self._send_json_response({
                        'success': False,
                        'errors': ['Thiếu mã cuộc họp']
                    }, 400)
                    return
                
                if not content.strip():
                    self._send_json_response({
                        'success': False,
                        'errors': ['Không có nội dung để lưu']
                    }, 400)
                    return
                
                # Lưu tài liệu
                result = save_meeting_documents(meeting_info, content)
                
                response = {
                    'success': len(result['errors']) == 0,
                    'folder': result['folder'],
                    'word': result['word'],
                    'pdf': result['pdf'],
                    'errors': result['errors']
                }
                
                self._send_json_response(response)
                
            except json.JSONDecodeError as e:
                self._send_json_response({
                    'success': False,
                    'errors': [f'Lỗi parse JSON: {str(e)}']
                }, 400)
            except Exception as e:
                self._send_json_response({
                    'success': False,
                    'errors': [f'Lỗi server: {str(e)}']
                }, 500)
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[API] {args[0]}")


def run_server(host='127.0.0.1', port=8766):
    """Chạy HTTP server"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, DocumentAPIHandler)
    print("=" * 60)
    print(f"Document API Server started on http://{host}:{port}")
    print("Endpoints:")
    print("  POST /save-document - Lưu tài liệu cuộc họp")
    print("=" * 60)
    httpd.serve_forever()


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
