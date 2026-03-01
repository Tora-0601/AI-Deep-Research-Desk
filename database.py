import sqlite3
from dataclasses import dataclass
from typing import Iterable, List

@dataclass
class Request:
    """ディープリサーチの依頼情報を表現するデータクラス"""
    date: str
    title: str
    requester: str
    email: str
    deadline: str
    topic: str
    prompt: str
    report: str
    correction: str
    # SQLiteの主キー（ID）用に追加（既存のコードを壊さないように最後にデフォルト値付きで追加）
    id: int = None

class Database:
    """SQLiteを使用して依頼データの永続化とデータアクセスを管理するリポジトリクラス"""
    
    def __init__(self, seed: Iterable[Request] | None = None) -> None:
        self.db_path = "research_requests.db"
        self._init_db()
        
        # 初期データ（seed）があり、かつDBが空の場合のみデータを挿入する
        if seed and self.get_count() == 0:
            for req in seed:
                self.add_request(req)

    def _get_connection(self):
        """データベース接続を取得する"""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """テーブルが存在しない場合は作成する"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    title TEXT,
                    requester TEXT,
                    email TEXT,
                    deadline TEXT,
                    topic TEXT,
                    prompt TEXT,
                    report TEXT,
                    correction TEXT
                )
            ''')
            conn.commit()

    def list_requests(self) -> List[Request]:
        """すべてのリクエストを最新順（降順）で取得する"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 最新の依頼が一番上に来るように ORDER BY id DESC を指定
            cursor.execute('SELECT date, title, requester, email, deadline, topic, prompt, report, correction, id FROM requests ORDER BY id DESC')
            rows = cursor.fetchall()
            return [Request(*row) for row in rows]

    def add_request(self, request: Request) -> None:
        """新しいリクエストをデータベースに保存する"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO requests (date, title, requester, email, deadline, topic, prompt, report, correction)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (request.date, request.title, request.requester, request.email, request.deadline, request.topic, request.prompt, request.report, request.correction))
            conn.commit()
            request.id = cursor.lastrowid

    def get_request(self, index: int) -> Request:
        """指定されたインデックスのリクエストを取得する"""
        requests = self.list_requests()
        if 0 <= index < len(requests):
            return requests[index]
        raise IndexError(f"無効なインデックス: {index}")

    def update_report(self, index: int, report: str) -> None:
        """レポート内容を更新する"""
        req = self.get_request(index)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE requests SET report = ? WHERE id = ?', (report, req.id))
            conn.commit()

    def update_correction(self, index: int, correction: str) -> None:
        """修正指示を更新する"""
        req = self.get_request(index)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE requests SET correction = ? WHERE id = ?', (correction, req.id))
            conn.commit()

    def delete_request(self, index: int) -> None:
        """指定されたインデックスのリクエストを削除する"""
        req = self.get_request(index)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM requests WHERE id = ?', (req.id,))
            conn.commit()

    def search_by_title(self, keyword: str) -> List[Request]:
        """タイトルで検索する"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT date, title, requester, email, deadline, topic, prompt, report, correction, id FROM requests WHERE title LIKE ? ORDER BY id DESC', (f'%{keyword}%',))
            rows = cursor.fetchall()
            return [Request(*row) for row in rows]

    def search_by_requester(self, requester: str) -> List[Request]:
        """依頼者名で検索する"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT date, title, requester, email, deadline, topic, prompt, report, correction, id FROM requests WHERE requester = ? ORDER BY id DESC', (requester,))
            rows = cursor.fetchall()
            return [Request(*row) for row in rows]

    def get_count(self) -> int:
        """保存されているリクエストの総数を取得する"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM requests')
            return cursor.fetchone()[0]