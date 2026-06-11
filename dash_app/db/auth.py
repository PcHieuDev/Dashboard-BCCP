# -*- coding: utf-8 -*-
"""
Module quản lý xác thực người dùng tích hợp với Flask-Login.
Định nghĩa class User và các hàm truy vấn tài khoản từ SQLite.
"""

import sqlite3
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from pathlib import Path
import sys

# Thêm thư mục gốc vào sys.path để import settings
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH

import logging
try:
    from config.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    try:
        from config.logger import get_logger
        logger = get_logger(__name__)
    except ImportError:
        logger = logging.getLogger(__name__)


class User(UserMixin):
    """Class User định nghĩa thông tin người dùng được quản lý bởi Flask-Login."""
    def __init__(self, user_id, username, role, assigned_cum=None):
        self.id = str(user_id)
        self.username = username
        self.role = role  # 'admin' hoặc 'user'
        self.assigned_cum = assigned_cum  # Tên Cụm được gán (nếu có)
        
    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def can_upload(self):
        """Admin và provincial_uploader mới có quyền upload dữ liệu."""
        return self.role in ['admin', 'provincial_uploader']

    @property
    def is_cluster_restricted(self):
        """cluster_viewer chỉ xem được dữ liệu của cụm được gán."""
        return self.role == 'cluster_viewer'

def get_user_by_id(user_id):
    """Lấy thông tin người dùng theo ID từ cơ sở dữ liệu SQLite."""
    if not DB_PATH.exists():
        return None
        
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, role, assigned_cum FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return User(user_id=row[0], username=row[1], role=row[2], assigned_cum=row[3])
    except Exception as e:
        logger.error(f"Lỗi khi tải user theo ID {user_id}: {e}")
    finally:
        conn.close()
    return None

def get_user_by_username(username):
    """Lấy thông tin người dùng theo tên đăng nhập."""
    if not DB_PATH.exists():
        return None
        
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, role, assigned_cum FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            return User(user_id=row[0], username=row[1], role=row[2], assigned_cum=row[3])
    except Exception as e:
        logger.error(f"Lỗi khi tải user theo username {username}: {e}")
    finally:
        conn.close()
    return None

def check_user_credentials(username, password):
    """
    Kiểm tra thông tin đăng nhập từ cơ sở dữ liệu.
    Trả về đối tượng User nếu hợp lệ, ngược lại trả về None.
    """
    if not DB_PATH.exists():
        return None
        
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, password_hash, role, assigned_cum FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            user_id, uname, pwd_hash, role, assigned_cum = row
            if check_password_hash(pwd_hash, password):
                return User(user_id=user_id, username=uname, role=role, assigned_cum=assigned_cum)
    except Exception as e:
        logger.error(f"Lỗi khi xác thực đăng nhập user {username}: {e}")
    finally:
        conn.close()
    return None
